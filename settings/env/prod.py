"""Settings for production: DEBUG off, PostgreSQL database."""

from decouple import config

from settings.base import *  # noqa: F403

DEBUG = False

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("COLLAB_POSTGRES_DB", cast=str),
        "USER": config("COLLAB_POSTGRES_USER", cast=str),
        "PASSWORD": config("COLLAB_POSTGRES_PASSWORD", cast=str),
        "HOST": config("COLLAB_POSTGRES_HOST", cast=str),
        "PORT": config("COLLAB_POSTGRES_PORT", cast=int),
    }
}
