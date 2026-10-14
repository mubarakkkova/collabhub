"""Admin filters for the users"""

from django.contrib.admin import ModelAdmin, SimpleListFilter
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import QuerySet


class IsDeletedListFilter(SimpleListFilter):
    title = "is deleted object"
    parameter_name = "is_deleted"

    DELETED_KEY = "deleted"
    NON_DELETED_KEY = "non-deleted"

    def lookups(
        self,
        request: WSGIRequest,
        model_admin: ModelAdmin,
    ) -> list[tuple[str, str]]:
        """return the filter options: value in the URL text for people."""

        return [
            (self.DELETED_KEY, "Deleted"),
            (self.NON_DELETED_KEY, "Not deleted"),
        ]

    def queryset(
        self,
        request: WSGIRequest,
        queryset: QuerySet,
    ) -> QuerySet:
        "filtering the rows by chosing option"
        if self.value() == self.DELETED_KEY:
            return queryset.filter(deleted_at__isnull=False)
        if self.value() == self.NON_DELETED_KEY:
            return queryset.filter(deleted_at__isnull=True)
        return queryset.all()
