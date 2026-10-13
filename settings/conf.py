"""Secrets from .env and settings of third-party libraries."""

from decouple import config

SECRET_KEY: str = config("COLLAB_SECRET_KEY", cast=str)
ENV_ID: str = config("COLLAB_ENV_ID", cast=str)
ADMIN_URL: str = config("COLLAB_ADMIN_URL", default="admin/", cast=str)
