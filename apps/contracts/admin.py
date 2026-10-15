from decimal import Decimal

from django.contrib.admin import (
    ModelAdmin,
    TabularInline,
    display,
    register,
)
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import F, QuerySet, Sum

from apps.contracts.models import Contract, ContractItem


class ContractItemInline(TabularInline):
    model = ContractItem
    extra = 1
    fields = (
        "content_type",
        "quantity",
        "price",
    )


@register(Contract)
class ContractAdmin(ModelAdmin):
    inlines = (ContractItemInline,)

    list_display = (
        "id",
        "collaboration",
        "total_amount",
        "deadline",
        "status",
        "items_count",
        "items_total",
    )
    list_display_links = (
        "id",
        "collaboration",
    )
    list_filter = (
        "status",
        "deadline",
    )
    search_fields = (
        "id",
        "collaboration__id",
    )
    search_help_text = "Search by contract ID or collaboration ID"
    list_select_related = ("collaboration",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_per_page = 25
    save_on_top = True
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    fieldsets = (
        (
            "General information",
            {
                "fields": (
                    "id",
                    "collaboration",
                    "status",
                ),
            },
        ),
        (
            "Financial details",
            {
                "fields": (
                    "total_amount",
                    "deadline",
                ),
            },
        ),
        (
            "Date and time information",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                    "deleted_at",
                ),
            },
        ),
    )

    def get_queryset(self, request: WSGIRequest) -> QuerySet:
        return (
            super()
            .get_queryset(request)
            .annotate(
                _items_count=Sum(
                    "items__quantity",
                    default=0,
                ),
                _items_total=Sum(
                    F("items__quantity") * F("items__price"),
                    default=Decimal("0.00"),
                ),
            )
        )

    @display(description="Items qty", ordering="_items_count")
    def items_count(self, obj: Contract) -> int:
        return obj._items_count  # noqa: ANN401

    @display(description="Computed total", ordering="_items_total")
    def items_total(self, obj: Contract) -> Decimal:
        return obj._items_total  # noqa: ANN401


@register(ContractItem)
class ContractItemAdmin(ModelAdmin):
    list_display = (
        "id",
        "contract",
        "content_type",
        "quantity",
        "price",
        "subtotal_display",
    )
    list_display_links = (
        "id",
        "contract",
    )
    list_filter = ("content_type",)
    search_fields = (
        "id",
        "contract__id",
    )
    search_help_text = "Search by item ID or contract ID"
    list_select_related = ("contract",)
    ordering = ("contract", "content_type")
    list_per_page = 25
    save_on_top = True
    readonly_fields = (
        "id",
        "subtotal_display",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    fieldsets = (
        (
            "General information",
            {
                "fields": (
                    "id",
                    "contract",
                    "content_type",
                ),
            },
        ),
        (
            "Pricing",
            {
                "fields": (
                    "quantity",
                    "price",
                    "subtotal_display",
                ),
            },
        ),
        (
            "Date and time information",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                    "deleted_at",
                ),
            },
        ),
    )

    @display(description="Subtotal")
    def subtotal_display(self, obj: ContractItem) -> Decimal:
        return obj.subtotal
