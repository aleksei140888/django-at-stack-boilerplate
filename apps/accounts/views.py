from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    PasswordChangeDoneView,
    PasswordChangeView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from . import services
from .forms import (
    CustomPasswordChangeForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm,
    DeleteAccountForm,
    LoginForm,
    ProfileForm,
    RegisterForm,
)

User = get_user_model()


def _safe_next(request) -> str:
    """
    Where to send the user after login/registration.

    ``?next=`` comes from the query string, so it is attacker-controlled: passing
    it to redirect() unchecked turns every auth page into an open redirect, which
    is what phishing links use to borrow this site's domain for credibility.
    """
    destination = request.GET.get("next", "")
    if destination and url_has_allowed_host_and_scheme(
        destination, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return destination
    return "/"


def register_view(request):
    if request.user.is_authenticated:
        return redirect("/")

    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = services.register_user(
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password1"],
            first_name=form.cleaned_data.get("first_name", ""),
            last_name=form.cleaned_data.get("last_name", ""),
        )
        # The backend has to be named explicitly: with allauth installed there
        # are two of them, and login() refuses to guess for a user that did not
        # come from authenticate().
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, _("Welcome! Your account has been created."))
        return redirect(_safe_next(request))

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
            "page_title": _("Create account"),
            "meta_description": _("Register a new account"),
        },
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("/")

    form = LoginForm(request, data=request.POST or None)
    if form.is_valid():
        user = form.get_user()
        remember_me = form.cleaned_data.get("remember_me")
        if not remember_me:
            request.session.set_expiry(0)
        login(request, user)
        services.touch_last_seen(user)
        messages.success(request, _("Welcome back!"))
        return redirect(_safe_next(request))

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
            "page_title": _("Log in"),
            "meta_description": _("Log in to your account"),
        },
    )


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, _("You have been logged out."))
    return redirect("/")


@login_required
def profile_view(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if form.is_valid():
        services.update_profile(request.user, **form.cleaned_data)
        messages.success(request, _("Profile updated."))
        return redirect("accounts:profile")

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "page_title": _("My profile"),
        },
    )


@login_required
def delete_account_view(request):
    form = DeleteAccountForm(request.user, request.POST or None)
    if form.is_valid():
        user = request.user
        logout(request)
        services.deactivate_account(user)
        messages.info(request, _("Your account has been deactivated."))
        return redirect("/")

    return render(
        request,
        "accounts/delete_account.html",
        {
            "form": form,
            "page_title": _("Delete account"),
        },
    )


class CustomPasswordChangeView(PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:password_change_done")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Change password")
        return ctx


class CustomPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = "accounts/password_change_done.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Password changed")
        return ctx


class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = "accounts/password_reset.html"
    email_template_name = "email/password_reset_email.html"
    subject_template_name = "email/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Reset password")
        ctx["meta_description"] = _("Reset your account password")
        return ctx


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Check your email")
        return ctx


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = CustomSetPasswordForm
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Set new password")
        return ctx


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Password reset complete")
        return ctx
