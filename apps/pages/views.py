from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _

from .forms import ContactForm


def home_view(request):
    return render(
        request,
        "pages/home.html",
        {
            "page_title": settings.SITE_NAME,
            "meta_description": _(
                "Django + Alpine.js + Tailwind CSS + DaisyUI — production-ready boilerplate."
            ),
            "schema_type": "WebSite",
        },
    )


def privacy_view(request):
    return render(
        request,
        "pages/privacy.html",
        {
            "page_title": _("Privacy Policy"),
            "meta_description": _("Read our Privacy Policy to understand how we handle your data."),
            "noindex": False,
        },
    )


def terms_view(request):
    return render(
        request,
        "pages/terms.html",
        {
            "page_title": _("Terms of Use"),
            "meta_description": _("Terms and conditions for using our service."),
        },
    )


def cookies_view(request):
    return render(
        request,
        "pages/cookies.html",
        {
            "page_title": _("Cookie Policy"),
            "meta_description": _("Learn about how we use cookies on our website."),
        },
    )


def contact_view(request):
    form = ContactForm(request.POST or None)
    if form.is_valid():
        name = form.cleaned_data["name"]
        email = form.cleaned_data["email"]
        message = form.cleaned_data["message"]
        send_mail(
            subject=f"Contact from {name}",
            message=f"From: {name} <{email}>\n\n{message}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.SERVER_EMAIL],
            fail_silently=True,
        )
        return redirect("pages:contact_done")

    return render(
        request,
        "pages/contact.html",
        {
            "form": form,
            "page_title": _("Contact us"),
            "meta_description": _("Get in touch with us."),
        },
    )


def contact_done_view(request):
    return render(
        request,
        "pages/contact_done.html",
        {
            "page_title": _("Message sent"),
        },
    )
