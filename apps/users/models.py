"""Models of the users app: the custom user, niches and profiles."""

from decimal import Decimal
from typing import Any

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db.models import (
    PROTECT,
    BooleanField,
    CharField,
    CheckConstraint,
    DecimalField,
    EmailField,
    ForeignKey,
    Index,
    ManyToManyField,
    OneToOneField,
    PositiveIntegerField,
    Q,
    SlugField,
    TextChoices,
    TextField,
    UniqueConstraint,
    URLField,
)

from apps.abstracts.models import AbstractBaseModel


class UserRole(TextChoices):
    """Who the user is on the platform."""

    BUSINESS = "business", "Business"
    BLOGGER = "blogger", "Blogger"


class SocialPlatform(TextChoices):
    """Social networks where a blogger publishes content."""

    INSTAGRAM = "instagram", "Instagram"
    TIKTOK = "tiktok", "TikTok"
    YOUTUBE = "youtube", "YouTube"
    TELEGRAM = "telegram", "Telegram"


class CustomUserManager(BaseUserManager):
    """Manager that knows how to create a user and a superuser correctly."""

    def create_user(
        self,
        email: str,
        full_name: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "CustomUser":
        """Create a user with a hashed password."""
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user: CustomUser = self.model(
            email=email,
            full_name=full_name,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        full_name: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "CustomUser":
        """Create a superuser: is_staff and is_superuser are turned on."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.BUSINESS)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(
            email=email,
            full_name=full_name,
            password=password,
            **extra_fields,
        )


class CustomUser(AbstractBaseUser, PermissionsMixin, AbstractBaseModel):
    """A platform user who logs in with email: a business or a blogger."""

    EMAIL_MAX_LEN = 254
    FULL_NAME_MAX_LEN = 150
    ROLE_MAX_LEN = 20

    email = EmailField(
        max_length=EMAIL_MAX_LEN,
        unique=True,
        verbose_name="email",
        help_text="Used instead of a username to log in.",
    )
    full_name = CharField(
        max_length=FULL_NAME_MAX_LEN,
        verbose_name="full name",
    )
    role = CharField(
        max_length=ROLE_MAX_LEN,
        choices=UserRole,
        default=UserRole.BUSINESS,
        db_index=True,
        verbose_name="role",
        help_text="Businesses create campaigns, bloggers apply to them.",
    )
    is_active = BooleanField(
        default=True,
        verbose_name="is active",
        help_text="Turn it off instead of deleting the account.",
    )
    is_staff = BooleanField(
        default=False,
        verbose_name="is staff",
        help_text="Allows logging in to the admin panel.",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "role"]

    objects = CustomUserManager()

    class Meta:
        """Meta class for CustomUser."""

        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        """Return the user representation for the admin and the shell."""
        return f"{self.full_name} ({self.email})"

    @property
    def is_business(self) -> bool:
        """Return True if the user is a business."""
        return self.role == UserRole.BUSINESS

    @property
    def is_blogger(self) -> bool:
        """Return True if the user is a blogger."""
        return self.role == UserRole.BLOGGER


class Niche(AbstractBaseModel):
    """An advertising niche: Beauty, Food, Tech and so on."""

    NAME_MAX_LEN = 100
    SLUG_MAX_LEN = 100

    name = CharField(
        max_length=NAME_MAX_LEN,
        verbose_name="niche name",
    )
    slug = SlugField(
        max_length=SLUG_MAX_LEN,
        verbose_name="slug",
        help_text="Short name for URLs: beauty, food, tech.",
    )
    description = TextField(
        blank=True,
        default="",
        verbose_name="description",
    )

    class Meta:
        """Meta class for Niche."""

        verbose_name = "niche"
        verbose_name_plural = "niches"
        ordering = ("name",)
        constraints = [
            UniqueConstraint(
                fields=("name",),
                condition=Q(deleted_at__isnull=True),
                name="unique_active_niche_name",
            ),
            UniqueConstraint(
                fields=("slug",),
                condition=Q(deleted_at__isnull=True),
                name="unique_active_niche_slug",
            ),
        ]

    def __str__(self) -> str:
        """Return the niche name."""
        return self.name


class BusinessProfile(AbstractBaseModel):
    """Extra information about a user with the business role."""

    COMPANY_NAME_MAX_LEN = 200
    CITY_MAX_LEN = 100

    user = OneToOneField(
        to=settings.AUTH_USER_MODEL,
        on_delete=PROTECT,
        related_name="business_profile",
        verbose_name="user",
    )
    company_name = CharField(
        max_length=COMPANY_NAME_MAX_LEN,
        verbose_name="company name",
    )
    description = TextField(
        blank=True,
        default="",
        verbose_name="description",
    )
    website = URLField(
        blank=True,
        default="",
        verbose_name="website",
    )
    city = CharField(
        max_length=CITY_MAX_LEN,
        blank=True,
        default="",
        verbose_name="city",
    )

    class Meta:
        """Meta class for BusinessProfile."""

        verbose_name = "business profile"
        verbose_name_plural = "business profiles"
        ordering = ("company_name",)

    def __str__(self) -> str:
        """Return the company name."""
        return self.company_name

    def clean(self) -> None:
        """Allow this profile only for a user with the business role."""
        if self.user_id and self.user.role != UserRole.BUSINESS:
            raise ValidationError(
                {"user": "This user is not a business."},
            )


class BloggerProfile(AbstractBaseModel):
    """Extra information about a user with the blogger role."""

    NICKNAME_MAX_LEN = 100
    CITY_MAX_LEN = 100
    PRICE_MAX_DIGITS = 10
    PRICE_DECIMAL_PLACES = 2

    user = OneToOneField(
        to=settings.AUTH_USER_MODEL,
        on_delete=PROTECT,
        related_name="blogger_profile",
        verbose_name="user",
    )
    nickname = CharField(
        max_length=NICKNAME_MAX_LEN,
        verbose_name="nickname",
        help_text="Public name of the blogger on the platform.",
    )
    bio = TextField(
        blank=True,
        default="",
        verbose_name="bio",
    )
    city = CharField(
        max_length=CITY_MAX_LEN,
        blank=True,
        default="",
        verbose_name="city",
    )
    niches = ManyToManyField(
        to="users.Niche",
        blank=True,
        related_name="bloggers",
        verbose_name="niches",
    )
    price_per_post = DecimalField(
        max_digits=PRICE_MAX_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=Decimal("0.00"),
        verbose_name="price per post",
        help_text="Price in KZT the blogger asks for one post.",
    )

    class Meta:
        """Meta class for BloggerProfile."""

        verbose_name = "blogger profile"
        verbose_name_plural = "blogger profiles"
        ordering = ("nickname",)
        constraints = [
            UniqueConstraint(
                fields=("nickname",),
                condition=Q(deleted_at__isnull=True),
                name="unique_active_blogger_nickname",
            ),
            CheckConstraint(
                condition=Q(price_per_post__gte=Decimal("0.00")),
                name="blogger_price_per_post_non_negative",
            ),
        ]

    def __str__(self) -> str:
        """Return the blogger nickname."""
        return f"@{self.nickname}"

    def clean(self) -> None:
        """Allow this profile only for a user with the blogger role."""
        if self.user_id and self.user.role != UserRole.BLOGGER:
            raise ValidationError(
                {"user": "This user is not a blogger."},
            )


class SocialAccount(AbstractBaseModel):
    """One social network account of a blogger with its followers count."""

    PLATFORM_MAX_LEN = 20
    USERNAME_MAX_LEN = 100

    blogger = ForeignKey(
        to="users.BloggerProfile",
        on_delete=PROTECT,
        related_name="social_accounts",
        verbose_name="blogger",
    )
    platform = CharField(
        max_length=PLATFORM_MAX_LEN,
        choices=SocialPlatform,
        verbose_name="platform",
    )
    username = CharField(
        max_length=USERNAME_MAX_LEN,
        verbose_name="username",
        help_text="Account name without the @ sign.",
    )
    profile_url = URLField(
        blank=True,
        default="",
        verbose_name="profile url",
    )
    followers_count = PositiveIntegerField(
        default=0,
        verbose_name="followers count",
    )
    is_verified = BooleanField(
        default=False,
        verbose_name="is verified",
        help_text="The blogger proved that the account belongs to them.",
    )

    class Meta:
        """Meta class for SocialAccount."""

        verbose_name = "social account"
        verbose_name_plural = "social accounts"
        ordering = ("-followers_count",)
        constraints = [
            UniqueConstraint(
                fields=("blogger", "platform"),
                condition=Q(deleted_at__isnull=True),
                name="unique_active_blogger_platform",
            ),
        ]
        indexes = [
            Index(
                fields=("platform", "-followers_count"),
                name="social_platform_followers_idx",
            ),
        ]

    def __str__(self) -> str:
        """Return the platform and the account name."""
        return f"{self.get_platform_display()}: @{self.username}"