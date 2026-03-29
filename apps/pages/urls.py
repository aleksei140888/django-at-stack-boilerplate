from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("privacy/", views.privacy_view, name="privacy"),
    path("terms/", views.terms_view, name="terms"),
    path("cookies/", views.cookies_view, name="cookies"),
    path("contact/", views.contact_view, name="contact"),
    path("contact/done/", views.contact_done_view, name="contact_done"),
]
