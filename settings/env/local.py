"""Settings for development: DEBUG on, SQLite database."""

from settings.base import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS: list[str] = []

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
    }
}
