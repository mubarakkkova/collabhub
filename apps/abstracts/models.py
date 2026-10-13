"""Abstract models shared by every app. No database tables are created here."""

from typing import Any

from django.db.models import DateTimeField, Model
from django.utils import timezone as django_timezone


class AbstractBaseModel(Model):
    """Abstract base model with common fields."""

    created_at = DateTimeField(
        auto_now_add=True,
    )
    updated_at = DateTimeField(
        auto_now=True,
    )
    deleted_at = DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        """Meta class for AbstractBaseModel."""

        abstract = True

    def delete(self, *args: Any, **kwargs: Any) -> None:
        """Soft delete the object by setting deleted_at timestamp."""
        self.deleted_at = django_timezone.now()
        self.save(update_fields=["deleted_at"])
