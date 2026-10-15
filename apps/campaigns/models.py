"""Advertising campaigns that businesses create for bloggers"""

from django.conf import settings
from django.db.models import (
    PROTECT,
    CharField,
    CheckConstraint,
    DateField,
    DecimalField,
    F,
    ForeignKey,
    Q,
    TextChoices,
    TextField,
    UniqueConstraint,
)
from django.utils import timezone

from apps.abstracts.models import AbstractBaseModel
from apps.users.models import UserRole


class CampaignPlatform(TextChoices):
    """Social platforms a campaign can run on."""

    INSTAGRAM = "instagram", "Instagram"
    TIKTOK = "tiktok", "Tiktok"
    YOUTUBE = "youtube", "Youtube"
    TELEGRAM = "telegram", "Telegram"


class CampaignStatus(TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    CLOSED = "closed", "Closed"


class Campaign(AbstractBaseModel):
    """One advertising campaign of a business."""

    TITLE_MAX_LENGTH = 200
    PLATFORM_MAX_LENGTH = 20
    STATUS_MAX_LENGTH = 20
    MONEY_MAX_DIGITS = 12
    MONEY_DECIMAL_PLACES = 2

    business = ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=PROTECT,
        related_name="campaigns",
        limit_choices_to={"role": UserRole.BUSINESS},
    )
    niche = ForeignKey(to="users.Niche", on_delete=PROTECT, related_name="campaigns")
    title = CharField(
        max_length=TITLE_MAX_LENGTH,
    )
    description = TextField(
        blank=True,
        default="",
    )
    platform = CharField(
        max_length=PLATFORM_MAX_LENGTH,
        choices=CampaignPlatform,
    )
    budget = DecimalField(
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        help_text="Total budget of the campaign, KZT",
    )
    start_date = DateField(
        help_text="First day of the campaign",
    )
    end_date = DateField(
        help_text="Last day of the campaign",
    )
    status = CharField(
        max_length=STATUS_MAX_LENGTH,
        choices=CampaignStatus,
        default=CampaignStatus.DRAFT,
    )

    class Meta:
        """Meta class for campaign"""

        verbose_name = "campaign"
        verbose_name_plural = "campaigns"
        ordering = ("-created_at",)
        constraints = [
            UniqueConstraint(
                fields=("business", "title"),
                condition=Q(deleted_at__isnull=True),
                name="unique_active_campaign_title_per_business",
            ),
            CheckConstraint(
                condition=Q(budget__gte=0),
                name="check_campaign_budget_non_negative",
            ),
            CheckConstraint(
                condition=Q(end_date__gte=F("start_date")),
                name="check_campaign_end_date_after_start_date",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_platform_display()})"

    @property
    def is_running(self) -> bool:
        """Campaign is active and today is inside its dates"""
        today = timezone.now().date()
        return (
            self.status == CampaignStatus.ACTIVE
            and self.start_date <= today <= self.end_date
        )

    @property
    def days_left(self) -> int:
        """Days from today to the end date, negative if it is over."""
        return (self.end_date - timezone.now().date()).days
