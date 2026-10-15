from decimal import Decimal

from django.db.models import (
    CASCADE,
    PROTECT,
    CharField,
    CheckConstraint,
    DateField,
    DecimalField,
    ForeignKey,
    Index,
    PositiveIntegerField,
    Q,
    TextChoices,
    UniqueConstraint,
)

from apps.abstracts.models import AbstractBaseModel


class ContractStatus(TextChoices):
    DRAFT = "draft", "Draft"
    AGREED = "agreed", "Agreed"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class ContentType(TextChoices):
    POST = "post", "Post"
    REELS = "reels", "Reels"
    STORY = "story", "Story"


class Contract(AbstractBaseModel):
    STATUS_MAX_LEN: int = 20
    TOTAL_AMOUNT_MAX_DIGITS: int = 12
    TOTAL_AMOUNT_DECIMAL_PLACES: int = 2

    collaboration = ForeignKey(
        to="collaborations.Collaboration",
        on_delete=PROTECT,
        related_name="contracts",
        verbose_name="collaboration",
    )
    total_amount = DecimalField(
        max_digits=TOTAL_AMOUNT_MAX_DIGITS,
        decimal_places=TOTAL_AMOUNT_DECIMAL_PLACES,
        default=Decimal("0.00"),
        verbose_name="total amount",
        help_text="Total contract amount in KZT.",
    )
    deadline = DateField(
        verbose_name="deadline",
        help_text="Date by which all deliverables must be submitted.",
    )
    status = CharField(
        max_length=STATUS_MAX_LEN,
        choices=ContractStatus,
        default=ContractStatus.DRAFT,
        db_index=True,
        verbose_name="status",
    )

    class Meta:
        verbose_name = "contract"
        verbose_name_plural = "contracts"
        ordering = ("-created_at",)
        constraints = [
            UniqueConstraint(
                fields=("collaboration",),
                condition=Q(deleted_at__isnull=True),
                name="unique_active_contract_per_collaboration",
            ),
            CheckConstraint(
                condition=Q(total_amount__gte=Decimal("0.00")),
                name="contract_total_amount_non_negative",
            ),
        ]
        indexes = [
            Index(
                fields=("status", "-created_at"),
                name="contract_status_created_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"Contract #{self.pk} — {self.get_status_display()}"


class ContractItem(AbstractBaseModel):
    CONTENT_TYPE_MAX_LEN: int = 20
    PRICE_MAX_DIGITS: int = 10
    PRICE_DECIMAL_PLACES: int = 2

    contract = ForeignKey(
        to="contracts.Contract",
        on_delete=CASCADE,
        related_name="items",
        verbose_name="contract",
    )
    content_type = CharField(
        max_length=CONTENT_TYPE_MAX_LEN,
        choices=ContentType,
        verbose_name="content type",
        help_text="What the blogger delivers: post, story or reels.",
    )
    quantity = PositiveIntegerField(
        default=1,
        verbose_name="quantity",
        help_text="How many pieces of this content type.",
    )
    price = DecimalField(
        max_digits=PRICE_MAX_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=Decimal("0.00"),
        verbose_name="price",
        help_text="Price per piece in KZT.",
    )

    class Meta:
        verbose_name = "contract item"
        verbose_name_plural = "contract items"
        ordering = ("contract", "content_type")
        constraints = [
            UniqueConstraint(
                fields=("contract", "content_type"),
                condition=Q(deleted_at__isnull=True),
                name="unique_active_contract_content_type",
            ),
            CheckConstraint(
                condition=Q(quantity__gte=1),
                name="contract_item_quantity_positive",
            ),
            CheckConstraint(
                condition=Q(price__gte=Decimal("0.00")),
                name="contract_item_price_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_content_type_display()} ×{self.quantity}"

    @property
    def subtotal(self) -> Decimal:
        return self.quantity * self.price
