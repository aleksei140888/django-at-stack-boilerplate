"""SEO surface: sitemap, robots.txt, canonical URLs and meta tags."""

import pytest

from django.urls import reverse

from apps.core.sitemaps import StaticViewSitemap


@pytest.mark.django_db
class TestSitemap:
    def test_sitemap_renders(self, client):
        response = client.get("/sitemap.xml")

        assert response.status_code == 200
        assert response["Content-Type"].startswith("application/xml")

    def test_every_listed_view_resolves(self):
        # A renamed URL leaves a dead entry in the sitemap, which is only ever
        # noticed in Search Console weeks later.
        for item in StaticViewSitemap().items():
            assert reverse(item)

    def test_public_pages_are_all_listed(self):
        listed = set(StaticViewSitemap().items())
        assert {"pages:home", "pages:privacy", "pages:terms", "pages:contact"} <= listed


@pytest.mark.django_db
class TestRobots:
    def test_robots_txt_points_at_the_sitemap(self, client, settings):
        response = client.get("/robots.txt")

        assert response.status_code == 200
        assert f"Sitemap: {settings.SITE_URL}/sitemap.xml" in response.content.decode()

    def test_private_areas_are_disallowed(self, client):
        body = client.get("/robots.txt").content.decode()

        assert "Disallow: /admin/" in body
        assert "Disallow: /accounts/" in body


@pytest.mark.django_db
class TestMetaTags:
    def test_canonical_url_is_absolute_and_matches_the_path(self, client, settings):
        response = client.get(reverse("pages:privacy"))
        html = response.content.decode()

        assert f'<link rel="canonical" href="{settings.SITE_URL}/privacy/">' in html

    def test_page_title_and_description_reach_the_html(self, client):
        html = client.get(reverse("pages:contact")).content.decode()

        assert "<title>" in html
        assert '<meta name="description" content="' in html

    def test_noindex_pages_say_so(self, client):
        # The health dashboard passes noindex=True — it must not be indexed.
        html = client.get(reverse("health")).content.decode()

        assert '<meta name="robots" content="noindex, nofollow">' in html

    def test_open_graph_image_is_absolute(self, client, settings):
        html = client.get(reverse("pages:home")).content.decode()

        assert f'content="{settings.SITE_URL}/static/img/og-default.png"' in html


@pytest.mark.django_db
class TestQueryBudget:
    """
    Page rendering must not grow queries with content.

    Add a case here whenever you add a list page; when you raise a budget, say in
    the pull request why the extra query is unavoidable.
    """

    @pytest.mark.parametrize(
        ("url_name", "max_queries"),
        [("pages:home", 3), ("pages:privacy", 3), ("pages:contact", 3)],
    )
    def test_anonymous_page_render_is_cheap(
        self, client, django_assert_max_num_queries, url_name, max_queries
    ):
        with django_assert_max_num_queries(max_queries):
            client.get(reverse(url_name))

    def test_authenticated_render_does_not_multiply_queries(
        self, client_authenticated, django_assert_max_num_queries
    ):
        # Session + user lookup is the whole budget; anything more means a view
        # is querying inside the template.
        with django_assert_max_num_queries(5):
            client_authenticated.get(reverse("pages:home"))
