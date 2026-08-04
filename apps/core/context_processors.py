from urllib.parse import urlparse

from django.conf import settings


def site_settings(request):
    # Origin of MEDIA_URL (a CDN host when S3 is configured) — used for a
    # <link rel="preconnect"> hint so the connection is warmed up before the
    # browser discovers the first <img> pointing there.
    media_url_parts = urlparse(settings.MEDIA_URL)
    media_origin = (
        f"{media_url_parts.scheme}://{media_url_parts.netloc}"
        if media_url_parts.scheme and media_url_parts.netloc
        else ""
    )

    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_URL": settings.SITE_URL,
        "DEBUG": settings.DEBUG,
        "APP_VERSION": settings.APP_VERSION,
        "MEDIA_ORIGIN": media_origin,
        # Where CSS/JS come from: the Vite dev server or the built bundle in
        # static/dist. Deriving it from DEBUG alone renders any DEBUG environment
        # without `npm run dev` running as unstyled HTML.
        "VITE_DEV_SERVER": settings.VITE_DEV_SERVER,
        "VITE_DEV_SERVER_URL": settings.VITE_DEV_SERVER_URL,
    }


def seo_defaults(request):
    """
    Default SEO context available on every page.

    ``canonical_url`` is built here and injected into the href in
    `partials/_meta_seo.html`. Templates must not override the ``canonical``
    block with a full <link> tag — Django passes an overridden block through
    `{% include %}` as a string, which would end up nested inside href="".
    """
    return {
        "default_og_image": f"{settings.SITE_URL}/static/img/og-default.png",
        "canonical_url": settings.SITE_URL + request.path,
        "og_image_width": 1200,
        "og_image_height": 630,
    }
