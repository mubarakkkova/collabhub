"""Admin panel for campaigns"""

from typing import Any

from django.contrib.admin import (
    EmptyFieldListFilter,
    ModelAdmin,
    action,
    display,
    register,
)
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest
from django.utils import timezone

from apps.campaigns.models import Campaign, CampaignStatus


class CampaignAdminForm(ModelForm):
    """Checks that one business has two active campaigns with one title."""

    class Meta:
        """Meta class for CampaignAdminForm."""

        model = Campaign
        fields = "__all__"

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        business = cleaned_data.get("business")
        title = cleaned_data.get("title")
        if business and title:
            duplicates = Campaign.objects.filter(
                business=business,
                title=title,
                deleted_at__isnull=True,
            )
            if self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise ValidationError(
                    f"This business already has a campaign named {title}."
                )
        return cleaned_data


@register(Campaign)
class CampaignAdmin(ModelAdmin):
    """Admin settings for Campaign."""

    form = CampaignAdminForm
    list_display = (
        "id",
        "title",
        "business",
        "niche",
        "platform",
        "budget",
        "start_date",
        "end_date",
        "days_left",
        "status",
        "is_running",
        "is_deleted",
    )
    list_display_links = ("id", "title")
    list_filter = (
        "status",
        "platform",
        "niche",
        "start_date",
        ("deleted_at", EmptyFieldListFilter),
    )
    search_fields = (
        "title",
        "description",
        "business__email",
        "business__full_name",
    )
    search_help_text = "Searche by title, description, business email or name"
    list_select_related = ("business", "niche")
    raw_id_fields = ("business",)
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at")
    date_hierarchy = "start_date"
    list_per_page = 25
    save_on_top = True
    actions = ("mark_active", "mark_closed")
    fieldsets = (
        ("Campaign", {"fields": ("id", "business", "title", "description")}),
        ("Where and how much", {"fields": ("niche", "platform", "budget")}),
        ("Dates and status", {"fields": ("start_date", "end_date", "status")}),
        (
            "System dates",
            {
                "fields": ("created_at", "updated_at", "deleted_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @display(description="Days left", ordering="end_date")
    def days_left(self, obj: Campaign) -> int:
        return obj.days_left

    @display(description="Running", boolean=True)
    def is_running(self, obj: Campaign) -> bool:
        return obj.is_running

    @display(description="Deleted", boolean=True)
    def is_deleted(self, obj: Campaign) -> bool:
        return obj.deleted_at is not None

    def has_delete_permission(
        self, request: HttpRequest, obj: Campaign | None = None
    ) -> bool:
        """Hide "Delete selected": it makes a real DELETE, not a soft one."""
        if obj is None or obj.deleted_at is not None:
            return False
        return super().has_delete_permission(request, obj)

    def get_deleted_objects(
        self, objs: QuerySet | list[Campaign], request: HttpRequest
    ) -> tuple[list[str], dict[str, int], set[str], list[str]]:
        """Soft delete keeps related rows, so PROTECT must not block it."""
        return [str(obj) for obj in objs], {}, set(), []

    @action(description="Mark selected as active")
    def mark_active(self, request: HttpRequest, queryset: QuerySet) -> None:
        changed = queryset.update(
            status=CampaignStatus.ACTIVE, updated_at=timezone.now()
        )
        self.message_user(request, f"Active: {changed}")

    @action(description="Mark selected as closed")
    def mark_closed(self, request: HttpRequest, queryset: QuerySet) -> None:
        changed = queryset.update(
            status=CampaignStatus.CLOSED, updated_at=timezone.now()
        )
        self.message_user(request, f"Closed: {changed}")
