from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/delete/", views.delete_account_view, name="delete_account"),
    # Password change
    path("password/change/", views.CustomPasswordChangeView.as_view(), name="password_change"),
    path(
        "password/change/done/",
        views.CustomPasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    # Password reset
    path("password/reset/", views.CustomPasswordResetView.as_view(), name="password_reset"),
    path(
        "password/reset/done/",
        views.CustomPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "password/reset/confirm/<uidb64>/<token>/",
        views.CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password/reset/complete/",
        views.CustomPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
