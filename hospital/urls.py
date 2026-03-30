"""
URL configuration for hospital project.
"""

from django.urls import include, path

urlpatterns = [
    path("", include("core.urls")),
]

handler404 = "core.views.custom_404"
