from django.urls import path

from . import api_views

app_name = "api"

urlpatterns = [
    path("health/", api_views.health_check, name="health"),
]
