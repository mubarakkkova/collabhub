"""Deliverables app: content published under a contract and reviews."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import (
    PROTECT,
    CharField,
    CheckConstraint,
    DateTimeField,
    F,
    ForeignKey,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    Q,
    TextChoices,
    TextField,
    UniqueConstraint,
    URLField,
)

from apps.abstracts.models import AbstractBaseModel


class Deliverable(AbstractBaseModel):
    """A post/story/video that the blogger published under a contract"""

    class Status(TextChoices):
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        NEEDS_CHANGES = "needs_changes", "Needs changes"

    STATUS_MAX_LEN = 20

    contract = ForeignKey(
        to="contracts.Contract",
        on_delete=PROTECT,
        related_name="deliverable",
        verbose_name="Contract",
    )
    post_url = URLField(
        verbose_name="Post link",
    )
    published_at = DateTimeField(
        verbose_name="Published at",
    )
    views = PositiveIntegerField(
        default=0,
        verbose_name="Views",
    )
    likes = PositiveIntegerField(
        default=0,
        verbose_name="Likes",
    )
    comments = PositiveIntegerField(
        default=0,
        verbose_name="Coments",
    )
    status = CharField(
        max_length=STATUS_MAX_LEN,
        choices=Status,
        default=Status.SUBMITTED,
        db_index=True,
        verbose_name="Status",
    )
    business_comment = TextField(
        blank=True,
        default="",
        verbose_name="Business comment",
        help_text="What the business wants to change",
    )

    class Meta:
        verbose_name = "Deliverable"
        verbose_name_plural = "Deliverables"
        ordering = ("-published_at",)
        constraints = (
            # the same post cannot be submitted twice for one contract
            UniqueConstraint(
                fields=("contract", "post_url"),
                condition=Q(deleted_at__isnull=True),
                name="unique_active_contract_post_url",
            )
        )

    def __str__(self) -> str:
        return f"{self.post_url} ({self.get_status_display()})"

    @property
    def engagement(self) -> int:
        "Likes + comments: how actively people reacted to the post"
        return self.likes + self.comments


class Review(AbstractBaseModel):
    """Feedback that one side of a contract leaves about the other side"""

    RATING_MIN = 1
    RATING_MAX = 5

    contract = ForeignKey(
        to="contracts.Contract",
        on_delete=PROTECT,
        related_name="reviews",
        verbose_name="Contract",
    )
    author = ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=PROTECT,
        related_name="reviews_written",
        verbose_name="Author",
    )
    target = ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=PROTECT,
        related_name="reviews_received",
        verbose_name="About whom",
    )
    rating = PositiveSmallIntegerField(
        validators=[MinValueValidator(RATING_MIN), MaxValueValidator(RATING_MAX)],
        verbose_name="Rating",
    )
    comment = TextField(
        blank=True,
        default="",
        verbose_name="Comment",
    )

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ("-created_at",)
        constraints = [
            # one review from each side per contract
            UniqueConstraint(
                fields=("contract", "author"),
                condition=Q(deleted_at__isnull=True),
                name="unique_active_review_per_contract_author",
            ),
            CheckConstraint(
                condition=Q(rating__gte=1) & Q(rating__lte=5),
                name="review_rating_1_5",
            ),
            CheckConstraint(
                condition=~Q(author=F("target")),
                name="review_author_not_target",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.rating}/5 from {self.author} to {self.target}"

    def clean(self) -> None:
        """Nobody can review themselves"""
        if self.author_id and self.author_id == self.target_id:
            raise ValidationError({"target": "You cannot review yourself"})
