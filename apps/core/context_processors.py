from django.conf import settings


def site_settings(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_URL": settings.SITE_URL,
        "DEBUG": settings.DEBUG,
    }


def seo_defaults(request):
    """Default SEO context available on every page."""
    return {
        "default_og_image": f"{settings.SITE_URL}/static/img/og-default.png",
        "canonical_url": settings.SITE_URL + request.path,
    }
