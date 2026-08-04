"""
Guards for the rules in DESIGN.md that a reviewer cannot reliably eyeball.

Only rules that are mechanically checkable live here. Whether a layout is
"asymmetric" or a colour is "oversaturated" is a judgement call and stays with
the reviewer; whether an emoji slipped into a template is not.
"""

import re
from pathlib import Path

import pytest

from django.urls import reverse

BASE_DIR = Path(__file__).resolve().parents[3]
TEMPLATES = sorted((BASE_DIR / "templates").rglob("*.html"))
MAIN_CSS = BASE_DIR / "static" / "src" / "css" / "main.css"

# Pictographs, emoticons, transport symbols, dingbats and the variation selector
# that turns a plain glyph into an emoji. Deliberately does not cover arrows and
# maths symbols, which are legitimate text.
EMOJI_RE = re.compile(
    "["
    "\U0001f300-\U0001f5ff"
    "\U0001f600-\U0001f64f"
    "\U0001f680-\U0001f6ff"
    "\U0001f900-\U0001f9ff"
    "\U00002700-\U000027bf"
    "️"
    "]"
)


def test_templates_are_found():
    # Without this, a moved template directory turns every test below into a
    # no-op that passes forever.
    assert TEMPLATES


@pytest.mark.parametrize("path", TEMPLATES, ids=lambda p: p.name)
def test_no_emoji_in_templates(path):
    """DESIGN.md: no emojis in UI — use an icon system (inline Lucide SVG here)."""
    found = EMOJI_RE.findall(path.read_text(encoding="utf-8"))
    assert not found, f"{path.name} contains emoji: {found}"


@pytest.mark.parametrize("path", TEMPLATES, ids=lambda p: p.name)
def test_no_h_screen(path):
    """DESIGN.md: `min-h-[100dvh]`, never `h-screen` — mobile browser chrome."""
    body = path.read_text(encoding="utf-8")
    assert not re.search(r"\bh-screen\b", body), f"{path.name} uses h-screen"
    assert not re.search(r"\bmin-h-screen\b", body), f"{path.name} uses min-h-screen"


@pytest.mark.parametrize("path", TEMPLATES, ids=lambda p: p.name)
def test_no_daisyui_4_classes(path):
    """`form-control`, `label-text` and `input-bordered` were removed in DaisyUI 5.

    They do not error — they simply stop applying, and the element quietly loses
    its styling. That is exactly the kind of regression nobody notices in a diff.
    """
    body = path.read_text(encoding="utf-8")
    for stale in ("form-control", "label-text", "input-bordered", "btn-outline"):
        assert stale not in body, f"{path.name} uses the DaisyUI 4 class {stale!r}"


class TestTheme:
    def test_single_dark_theme_is_declared(self):
        css = MAIN_CSS.read_text(encoding="utf-8")
        assert 'name: "cybertribal"' in css
        assert "color-scheme: dark" in css

    def test_base_radius_is_eight_pixels(self):
        css = MAIN_CSS.read_text(encoding="utf-8")
        for token in ("--radius-box", "--radius-field", "--radius-selector"):
            assert f"{token}: 0.5rem" in css

    def test_reduced_motion_is_honoured(self):
        assert "prefers-reduced-motion" in MAIN_CSS.read_text(encoding="utf-8")

    def test_palette_hexes_from_design_md_are_present(self):
        """Every colour DESIGN.md names appears as an oklch comment in the theme.

        The theme stores oklch so DaisyUI can mix it; the hex in the trailing
        comment is what makes the connection back to DESIGN.md greppable.
        """
        css = MAIN_CSS.read_text(encoding="utf-8")
        for hex_value in ("#00FFFF", "#29AB87", "#FF00FF", "#4B0082", "#FF4500", "#BF00FF"):
            assert hex_value in css, f"palette colour {hex_value} is not in the theme"


@pytest.mark.django_db
class TestRenderedPages:
    def test_theme_attribute_is_set_on_every_page(self, client):
        html = client.get(reverse("pages:home")).content.decode()
        assert 'data-theme="cybertribal"' in html

    def test_theme_color_meta_matches_the_dark_surface(self, client):
        html = client.get(reverse("pages:home")).content.decode()
        assert '<meta name="theme-color" content="#08040F">' in html

    def test_no_light_theme_toggle_remains(self, client):
        # The design is dark-only; a leftover toggle would switch to a theme
        # that no longer exists and leave the page unstyled.
        html = client.get(reverse("pages:home")).content.decode()
        assert "themeManager" not in html
        assert "toggleTheme" not in html
