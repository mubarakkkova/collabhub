"""Abstract models shared by every app. No database tables are created here."""

from typing import Any

from django.db.models import DateTimeField, Manager, Model, QuerySet
from django.utils import timezone as django_timezone


class AliveManager(Manager):
    """Manager with alive():  only row that not soft deleted"""

    def alive(self) -> QuerySet:
        """Return the objects whose deleted_at is empty"""
        return self.get_queryset().filter(deleted_at__isnull=True)


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

    objects = AliveManager()

    class Meta:
        """Meta class for AbstractBaseModel."""

        abstract = True

    def delete(self, *args: Any, **kwargs: Any) -> None:
        """Soft delete the object by setting deleted_at timestamp."""
        self.deleted_at = django_timezone.now()
        self.save(update_fields=["deleted_at"])
