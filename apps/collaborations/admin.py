"""Admin panel for collaborations and their status history."""

from django.contrib.admin import (
    EmptyFieldListFilter,
    ModelAdmin,
    TabularInline,
    action,
    display,
    register,
)
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.collaborations.models import (
    Collaboration,
    CollaborationStatus,
    CollaborationStatusHistory,
)


class CollaborationStatusHistoryInline(TabularInline):
    """Shows the status history inside the collaboration page (read only)."""

    model = CollaborationStatusHistory
    extra = 0
    can_delete = False
    fields = ("old_status", "new_status", "comment", "created_at")
    readonly_fields = ("old_status", "new_status", "created_at")

    def has_add_permission(
        self, request: HttpRequest, obj: Collaboration | None = None
    ) -> bool:
        return False


@register(Collaboration)
class CollaborationAdmin(ModelAdmin):
    """Admin settings for Collaboration."""

    list_display = (
        "id",
        "campaign",
        "blogger",
        "offered_price",
        "status",
        "created_at",
        "is_deleted",
    )
    list_display_links = ("id", "campaign")
    list_filter = (
        "status",
        "campaign__platform",
        "campaign__niche",
        "created_at",
        ("deleted_at", EmptyFieldListFilter),
    )
    search_fields = (
        "campaign__title",
        "blogger__email",
        "blogger__full_name",
        "message",
    )
    search_help_text = "Search by campaign title, blogger email or name, message"
    list_select_related = ("campaign", "blogger")

    raw_id_fields = ("campaign", "blogger")
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at")
    date_hierarchy = "created_at"
    list_per_page = 25
    save_on_top = True
    inlines = (CollaborationStatusHistoryInline,)
    actions = ("mark_accepted", "mark_rejected")
    fieldsets = (
        ("Application", {"fields": ("id", "campaign", "blogger", "message")}),
        ("Conditions", {"fields": ("offered_price", "status")}),
        (
            "Dates",
            {
                "fields": ("created_at", "updated_at", "deleted_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @display(description="Deleted", boolean=True)
    def is_deleted(self, obj: Collaboration) -> bool:
        return obj.deleted_at is not None

    def has_delete_permission(
        self, request: HttpRequest, obj: Collaboration | None = None
    ) -> bool:
        """Hide "Delete selected": it makes a real DELETE, not a soft one."""
        if obj is None or obj.deleted_at is not None:
            return False
        return super().has_delete_permission(request, obj)

    def get_deleted_objects(
        self, objs: QuerySet | list[Collaboration], request: HttpRequest
    ) -> tuple[list[str], dict[str, int], set[str], list[str]]:
        """Soft delete keeps related rows, so PROTECT must not block it."""
        return [str(obj) for obj in objs], {}, set(), []

    def set_status(self, queryset: QuerySet, status: str) -> int:
        """Change status one by one, so save() writes the history."""
        changed = 0
        for collaboration in queryset:
            if collaboration.status != status:
                collaboration.status = status
                collaboration.save(update_fields=["status", "updated_at"])
                changed += 1
        return changed

    @action(description="Mark selected as accepted")
    def mark_accepted(self, request: HttpRequest, queryset: QuerySet) -> None:
        changed = self.set_status(queryset, CollaborationStatus.ACCEPTED)
        self.message_user(request, f"Accepted: {changed}")

    @action(description="Mark selected as rejected")
    def mark_rejected(self, request: HttpRequest, queryset: QuerySet) -> None:
        changed = self.set_status(queryset, CollaborationStatus.REJECTED)
        self.message_user(request, f"Rejected: {changed}")


@register(CollaborationStatusHistory)
class CollaborationStatusHistoryAdmin(ModelAdmin):
    """Read-only log of all status changes."""

    list_display = ("id", "collaboration", "old_status", "new_status", "created_at")
    list_filter = ("new_status", "created_at")
    search_fields = ("collaboration__campaign__title", "collaboration__blogger__email")
    list_select_related = ("collaboration__campaign", "collaboration__blogger")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(
        self,
        request: HttpRequest,
        obj: CollaborationStatusHistory | None = None,
    ) -> bool:
        return False

    def has_delete_permission(
        self,
        request: HttpRequest,
        obj: CollaborationStatusHistory | None = None,
    ) -> bool:
        return False
