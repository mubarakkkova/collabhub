from django.contrib.admin import ModelAdmin, action, display, register
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from apps.deliverables.models import Deliverable, Review


class SoftDeleteAdmin(ModelAdmin):
    """Keeps soft delete safe in the admin"""

    def has_delete_permission(
        self, request: HttpRequest, obj: Deliverable | Review | None = None
    ) -> bool:
        if obj is None or obj.deleted_at is not None:
            return False
        return super().has_delete_permission(request, obj)


@register(Deliverable)
class DeliverableAdmin(SoftDeleteAdmin):
    list_display = (
        "id",
        "contract",
        "status",
        "views",
        "likes",
        "comments",
        "engagement",
        "published_at",
        "is_deleted",
    )
    list_display_links = ("id", "contract")
    list_filter = ("status", "published_at")
    search_fields = ("post_url", "business_comment")
    list_select_related = ("contract",)
    raw_id_fields = ("contract",)
    date_hierarchy = "published_at"
    readonly_fields = ("created_at", "updated_at", "deleted_at")
    list_per_page = 50
    save_on_top = True
    actions = ("mark_approved", "mark_needs_changes")
    fieldsets = (
        ("Publication", {"fields": ("contract", "post_url", "published_at")}),
        ("Statistics", {"fields": (("views", "likes", "comments"),)}),
        ("Review by business", {"fields": ("status", "business_comment")}),
        (
            "Date and time information",
            {"fields": ("created_at", "updated_at", "deleted_at")},
        ),
    )

    @display(description="Post")
    def post_link(self, obj: Deliverable) -> str:
        return format_html('<a href="{}" target="_blank">open</a>', obj.post_url)

    @display(description="Engagement")
    def engagement(self, obj: Deliverable) -> int:
        return obj.engagement

    @display(description="Deleted", boolean=True)
    def is_deleted(self, obj: Deliverable) -> bool:
        return obj.deleted_at is not None

    @action(description="Approve selected deliverables")
    def mark_approved(
        self, request: HttpRequest, queryset: QuerySet[Deliverable]
    ) -> None:
        updated: int = queryset.update(status=Deliverable.Status.APPROVED)
        self.message_user(request, f"{updated} deliverable(s) approved")

    @action(description="Send selected back for changes")
    def mark_needs_changes(
        self, request: HttpRequest, queryset: QuerySet[Deliverable]
    ) -> None:
        updated: int = queryset.update(status=Deliverable.Status.NEEDS_CHANGES)
        self.message_user(request, f"{updated} deliverable(s) sent back")


@register(Review)
class ReviewAdmin(SoftDeleteAdmin):
    list_display = (
        "id",
        "contract",
        "author",
        "target",
        "stars",
        "created_at",
        "is_deleted",
    )
    list_display_links = ("id", "contract")
    list_filter = ("rating", "created_at")
    search_fields = ("author__email", "target__email", "comment")
    list_select_related = ("contract", "author", "target")
    raw_id_fields = ("contract", "author", "target")
    readonly_fields = ("created_at", "updated_at", "deleted_at")
    list_per_page = 50

    @display(description="Rating", ordering="ratting")
    def stars(self, obj: Review) -> str:
        return "⭑" * obj.rating + "☆" * (Review.RATING_MAX - obj.rating)

    @display(description="Deleted", boolean=True)
    def is_deleted(self, obj: Review) -> bool:
        return obj.deleted_at is not None
