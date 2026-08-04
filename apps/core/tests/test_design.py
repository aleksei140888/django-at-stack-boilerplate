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
    def test_both_themes_are_declared(self):
        css = MAIN_CSS.read_text(encoding="utf-8")
        assert 'name: "cybertribal"' in css
        assert 'name: "cybertribal-light"' in css
        assert "color-scheme: dark" in css
        assert "color-scheme: light" in css

    def test_dark_is_the_default(self):
        """Dark is the design; light is its companion, not a coin flip."""
        css = MAIN_CSS.read_text(encoding="utf-8")
        dark_block = css[css.index('name: "cybertribal";') : css.index('name: "cybertribal-light"')]
        assert "default: true" in dark_block

    def test_light_theme_drops_the_neon(self):
        """A glow needs darkness; on off-white it turns into grey haze."""
        css = MAIN_CSS.read_text(encoding="utf-8")
        light_overrides = css[css.index('[data-theme="cybertribal-light"]') :]
        assert "background-image: none" in light_overrides  # no blacklight wash
        assert "text-shadow: none" in light_overrides  # no glowing text

    def test_light_theme_surface_is_not_pure_white(self):
        # DESIGN.md's do-not list, and the reason base-100 carries a violet cast.
        # Comments are stripped first: the block names #FFFFFF to say it avoids it.
        css = MAIN_CSS.read_text(encoding="utf-8")
        light_block = css.split('name: "cybertribal-light"')[1].split("}")[0]
        declarations = re.sub(r"/\*.*?\*/", "", light_block, flags=re.DOTALL)

        assert "#F5F2FA" in css
        assert "#FFFFFF" not in declarations
        # oklch lightness of 100% is white whatever the hex comment claims.
        assert "--color-base-100: oklch(100" not in declarations

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

    def test_theme_color_meta_starts_on_the_dark_surface(self, client):
        # themeManager rewrites this when the theme changes; a meta tag cannot
        # follow data-theme from CSS.
        html = client.get(reverse("pages:home")).content.decode()
        assert '<meta name="theme-color" content="#08040F">' in html

    def test_the_switcher_is_wired_up(self, client):
        html = client.get(reverse("pages:home")).content.decode()
        assert 'x-data="themeManager()"' in html
        assert "toggleTheme()" in html

    def test_theme_is_resolved_before_first_paint(self, client):
        """The inline script is what prevents a full-page flash on load.

        Alpine boots after paint, so without it the first frame is drawn in the
        wrong theme and then corrects itself.
        """
        head = client.get(reverse("pages:home")).content.decode().split("</head>")[0]

        assert "prefers-color-scheme: light" in head
        assert "localStorage.getItem" in head
        # Before the bundle: a module script would run after paint either way.
        assert head.index("localStorage.getItem") < head.index("dist/main.js")

    def test_stored_theme_is_validated_before_first_paint(self, client):
        """The inline script must check the stored value against an allow-list.

        It is a copy of resolveTheme() in theme.js (tested there) and can drift.
        A value left by an older build would otherwise be written to data-theme
        verbatim, pinning the page to a theme that has no rules.
        """
        head = client.get(reverse("pages:home")).content.decode().split("</head>")[0]
        script = head[head.index("<script>") : head.index("</script>")]

        assert '"cybertribal"' in script
        assert '"cybertribal-light"' in script
        assert "indexOf" in script
