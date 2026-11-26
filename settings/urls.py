"""Main list of URLs of the CollabHub project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path

from settings.conf import ADMIN_URL

urlpatterns: list[URLPattern | URLResolver] = [
    path(ADMIN_URL, admin.site.urls),
    path("api/users/", include("apps.users.urls")),
    path("api/campaigns/", include("apps.campaigns.urls")),
    path("api/collaborations/", include("apps.collaborations.urls")),
    path("api/contracts/", include("apps.contracts.urls")),
    path("api/deliverables/", include("apps.deliverables.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
