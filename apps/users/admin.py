"""admin panel configuration of the users app."""

from django.contrib.admin import (
    ModelAdmin,
    StackedInline,
    TabularInline,
    display,
    register,
)
from django.contrib.auth.admin import UserAdmin
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Count, Q, QuerySet, Sum
from django.utils.html import format_html

from apps.users.filters import IsDeletedListFilter
from apps.users.forms import (
    CustomUserChangeForm,
    CustomUserCreationForm,
    NicheAdminForm,
)
from apps.users.models import (
    BloggerProfile,
    BusinessProfile,
    CustomUser,
    Niche,
    SocialAccount,
)


class BusinessProfileInline(StackedInline):
    """Business profile right on the user page."""

    model = BusinessProfile
    extra = 0
    can_delete = False
    verbose_name_plural = "Business profile"
    fields = (
        "company_name",
        "website",
        "city",
        "description",
    )


class BloggerProfileInline(StackedInline):
    """Blogger profile right on the user page."""

    model = BloggerProfile
    extra = 0
    can_delete = False
    verbose_name_plural = "Blogger profile"
    filter_horizontal = ("niches",)
    fields = (
        "nickname",
        "price_per_post",
        "city",
        "niches",
        "bio",
    )


class SocialAccountInline(TabularInline):
    """Social accounts right on the blogger profile page."""

    model = SocialAccount
    extra = 1
    fields = (
        "platform",
        "username",
        "profile_url",
        "followers_count",
        "is_verified",
    )


@register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """CustomUser admin configuration class."""

    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = (
        "id",
        "email",
        "full_name",
        "role",
        "is_active",
        "is_staff",
        "deleted_status",
    )
    list_display_links = (
        "id",
        "email",
    )
    list_filter = (
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
        IsDeletedListFilter,
    )
    search_fields = (
        "id",
        "email",
        "full_name",
    )
    search_help_text = "Search by ID, email or full name"
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_per_page = 25
    save_on_top = True
    filter_horizontal = (
        "groups",
        "user_permissions",
    )
    readonly_fields = (
        "id",
        "last_login",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    fieldsets = (
        (
            "Credentials",
            {
                "fields": (
                    "id",
                    "email",
                    "password",
                ),
            },
        ),
        (
            "General information",
            {
                "fields": (
                    "full_name",
                    "role",
                ),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    ("is_active", "is_staff"),
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Date and time information",
            {
                "classes": ("collapse",),
                "fields": (
                    "last_login",
                    "created_at",
                    "updated_at",
                    "deleted_at",
                ),
            },
        ),
    )
    add_fieldsets = (
        (
            "Credentials",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                ),
            },
        ),
        (
            "General information",
            {
                "fields": (
                    "full_name",
                    "role",
                ),
            },
        ),
    )

    @display(description="Status")
    def deleted_status(self, obj: CustomUser) -> str:
        """Show the soft delete mark as a colored word."""
        color, label = ("red", "Deleted") if obj.deleted_at else ("green", "Active")
        return format_html('<b style="color: {};">{}</b>', color, label)

    def get_readonly_fields(
        self,
        request: WSGIRequest,
        obj: CustomUser | None = None,
    ) -> tuple[str, ...]:
        """Forbid changing the email after the user is created."""
        if obj is not None:
            return ("email", *self.readonly_fields)
        return self.readonly_fields

    def get_inlines(
        self,
        request: WSGIRequest,
        obj: CustomUser | None = None,
    ) -> list[type[StackedInline]]:
        """Show the profile inline that matches the role of the user."""
        if obj is None:
            return []
        if obj.is_business:
            return [BusinessProfileInline]
        return [BloggerProfileInline]

    def has_delete_permission(
        self,
        request: WSGIRequest,
        obj: CustomUser | None = None,
    ) -> bool:
        """Hide the bulk delete action and forbid deleting yourself."""
        if obj is None:
            return False
        if obj == request.user:
            return False
        return super().has_delete_permission(request, obj)


@register(Niche)
class NicheAdmin(ModelAdmin):
    """Niche admin configuration class."""

    form = NicheAdminForm

    list_display = (
        "id",
        "name",
        "slug",
        "bloggers_count",
        "deleted_status",
    )
    list_display_links = (
        "id",
        "name",
    )
    list_filter = (IsDeletedListFilter,)
    search_fields = (
        "name",
        "slug",
    )
    search_help_text = "Search by name or slug"
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    list_per_page = 25
    save_on_top = True
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    fields = (
        "id",
        "name",
        "slug",
        "description",
        ("created_at", "updated_at"),
        "deleted_at",
    )

    def get_queryset(self, request: WSGIRequest) -> QuerySet:
        """Count the bloggers of every niche in one query instead of N."""
        return (
            super()
            .get_queryset(request)
            .annotate(
                bloggers_total=Count(
                    "bloggers",
                    filter=Q(bloggers__deleted_at__isnull=True),
                    distinct=True,
                ),
            )
        )

    @display(description="Bloggers", ordering="bloggers_total")
    def bloggers_count(self, obj: Niche) -> int:
        """Show how many bloggers work in this niche."""
        return obj.bloggers_total

    @display(description="Status")
    def deleted_status(self, obj: Niche) -> str:
        """Show the soft delete mark as a colored word."""
        color, label = ("red", "Deleted") if obj.deleted_at else ("green", "Active")
        return format_html('<b style="color: {};">{}</b>', color, label)


@register(BusinessProfile)
class BusinessProfileAdmin(ModelAdmin):
    """BusinessProfile admin configuration class."""

    list_display = (
        "id",
        "company_name",
        "user",
        "city",
        "website",
    )
    list_display_links = (
        "id",
        "company_name",
    )
    list_filter = (
        "city",
        IsDeletedListFilter,
    )
    search_fields = (
        "company_name",
        "user__email",
        "user__full_name",
    )
    search_help_text = "Search by company name or by the email of the user"
    list_select_related = ("user",)
    autocomplete_fields = ("user",)
    ordering = ("company_name",)
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
                    "user",
                    "company_name",
                    "description",
                ),
            },
        ),
        (
            "Contacts",
            {
                "fields": (
                    "website",
                    "city",
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


@register(BloggerProfile)
class BloggerProfileAdmin(ModelAdmin):
    """BloggerProfile admin configuration class."""

    inlines = (SocialAccountInline,)

    list_display = (
        "id",
        "nickname",
        "user",
        "city",
        "price_per_post",
        "followers_total_count",
    )
    list_display_links = (
        "id",
        "nickname",
    )
    list_filter = (
        "niches",
        "city",
        IsDeletedListFilter,
    )
    search_fields = (
        "nickname",
        "user__email",
        "user__full_name",
    )
    search_help_text = "Search by nickname or by the email of the user"
    list_select_related = ("user",)
    autocomplete_fields = ("user",)
    filter_horizontal = ("niches",)
    ordering = ("nickname",)
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
                    "user",
                    "nickname",
                    "bio",
                ),
            },
        ),
        (
            "Work",
            {
                "fields": (
                    "niches",
                    "price_per_post",
                    "city",
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
        """Sum the followers of every blogger in one query instead of N."""
        return (
            super()
            .get_queryset(request)
            .annotate(
                followers_total=Sum(
                    "social_accounts__followers_count",
                    filter=Q(social_accounts__deleted_at__isnull=True),
                ),
            )
        )

    @display(description="Followers", ordering="followers_total")
    def followers_total_count(self, obj: BloggerProfile) -> int:
        """Show the followers of all social accounts of the blogger."""
        return obj.followers_total or 0


@register(SocialAccount)
class SocialAccountAdmin(ModelAdmin):
    """SocialAccount admin configuration class."""

    list_display = (
        "id",
        "blogger",
        "platform",
        "username",
        "followers_count",
        "is_verified",
    )
    list_display_links = (
        "id",
        "username",
    )
    list_filter = (
        "platform",
        "is_verified",
        IsDeletedListFilter,
    )
    search_fields = (
        "username",
        "blogger__nickname",
    )
    search_help_text = "Search by account name or blogger nickname"
    list_select_related = ("blogger",)
    autocomplete_fields = ("blogger",)
    list_editable = ("followers_count",)
    ordering = ("-followers_count",)
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
                    "blogger",
                    "platform",
                    "username",
                    "profile_url",
                ),
            },
        ),
        (
            "Statistics",
            {
                "fields": (("followers_count", "is_verified"),),
            },
        ),
        (
            "Date and time info",
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
