"""
URL configuration for hospital project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path

urlpatterns = [
    path("", include("core.urls")),
]

handler404 = "core.views.custom_404"

# Always expose media files when running this Django app directly
# so uploaded hospital images work even if DEBUG is false in local demos.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

