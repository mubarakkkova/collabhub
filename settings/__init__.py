"""Load the Celery app together with Django combo"""

from settings.celery import app as celery_app

__all__ = ("celery_app",)
