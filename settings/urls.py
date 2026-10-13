"""Main list of URLs of the CollabHub project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import URLPattern, URLResolver, path

from settings.conf import ADMIN_URL

urlpatterns: list[URLPattern | URLResolver] = [
    path(ADMIN_URL, admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
