"""Blogger applications to campaigns and the history of their statuses."""

from typing import Any

from django.conf import settings
from django.db.models import (
    PROTECT,
    CharField,
    CheckConstraint,
    DecimalField,
    ForeignKey,
    Q,
    TextChoices,
    TextField,
    UniqueConstraint,
)

from apps.abstracts.models import AbstractBaseModel
from apps.users.models import UserRole


class CollaborationStatus(TextChoices):
    """Possible statuses for a collaboration."""

    SENT = "sent", "Sent"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"


class Collaboration(AbstractBaseModel):
    """An application of a blogger to a campaign."""

    STATUS_MAX_LENGTH = 20
    PRICE_MAX_DIGITS = 12
    PRICE_DECIMAL_PLACES = 2

    campaign = ForeignKey(
        to="campaigns.Campaign",
        on_delete=PROTECT,
        related_name="collaborations",
    )

    blogger = ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=PROTECT,
        related_name="collaborations",
        limit_choices_to={"role": UserRole.BLOGGER},
    )

    message = TextField(
        blank=True,
        default="",
        help_text="Message from the blogger to the business",
    )
    offered_price = DecimalField(
        max_digits=PRICE_MAX_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        help_text="Price offered by the blogger, KZT",
    )
    status = CharField(
        max_length=STATUS_MAX_LENGTH,
        choices=CollaborationStatus,
        default=CollaborationStatus.SENT,
    )

    class Meta:
        """Meta class for Collaboration."""

        verbose_name = "collaboration"
        verbose_name_plural = "collaborations"
        ordering = ("-created_at",)
        constraints = [
            UniqueConstraint(
                fields=("campaign", "blogger"),
                condition=Q(deleted_at__isnull=True),
                name="unique_active_collaboration_campaign_blogger",
            ),
            CheckConstraint(
                condition=Q(offered_price__gte=0),
                name="check_offered_price_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.blogger} -> {self.campaign} ({self.status})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the collaboration and write a history row if status changed."""
        old_status: str | None = None
        if self.pk:
            old_status = (
                Collaboration.objects.filter(pk=self.pk)
                .values_list("status", flat=True)
                .first()
            )
        super().save(*args, **kwargs)
        if old_status != self.status:
            CollaborationStatusHistory.objects.create(
                collaboration=self,
                old_status=old_status or "",
                new_status=self.status,
            )


class CollaborationStatusHistory(AbstractBaseModel):
    """One change of collaboration status: from old_status to new_status."""

    STATUS_MAX_LENGTH = 20

    collaboration = ForeignKey(
        to=Collaboration,
        on_delete=PROTECT,
        related_name="status_history",
    )
    old_status = CharField(
        max_length=STATUS_MAX_LENGTH,
        choices=CollaborationStatus,
        blank=True,
        default="",
    )
    new_status = CharField(
        max_length=STATUS_MAX_LENGTH,
        choices=CollaborationStatus,
    )
    comment = TextField(
        blank=True,
        default="",
    )

    class Meta:
        """Meta class for CollaborationStatusHistory."""

        verbose_name = "status change"
        verbose_name_plural = "status history"
        ordering = ("created_at",)

    def __str__(self) -> str:
        old = self.old_status or "-"
        return f"#{self.collaboration_id}: {old} -> {self.new_status}"
