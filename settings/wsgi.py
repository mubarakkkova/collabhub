"""Entry point for a regular (WSGI) web server."""

import os

from django.core.handlers.wsgi import WSGIHandler
from django.core.wsgi import get_wsgi_application

from settings.conf import ENV_ID

assert ENV_ID, "Environmental value is not set"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"settings.env.{ENV_ID}")

application: WSGIHandler = get_wsgi_application()
