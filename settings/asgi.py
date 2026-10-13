"""Entry point for an async (ASGI) web server."""

import os

from django.core.asgi import get_asgi_application
from django.core.handlers.asgi import ASGIHandler

from settings.conf import ENV_ID

assert ENV_ID, "Environmental value is not set"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"settings.env.{ENV_ID}")

application: ASGIHandler = get_asgi_application()
