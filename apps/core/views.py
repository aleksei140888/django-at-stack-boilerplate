from django.shortcuts import render
from django.utils.translation import gettext_lazy as _


def health_page(request):
    return render(
        request,
        "core/health.html",
        {
            "page_title": _("System Health"),
            "noindex": True,
        },
    )


def handler404(request, exception=None):
    return render(request, "errors/404.html", status=404)


def handler403(request, exception=None):
    return render(request, "errors/403.html", status=403)


def handler500(request):
    return render(request, "errors/500.html", status=500)
