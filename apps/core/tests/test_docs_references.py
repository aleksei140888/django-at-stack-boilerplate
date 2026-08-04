"""
Guard the documentation against silent drift.

Docs are how an agent (or a new developer) finds its way around, and a link that
404s costs more than a missing paragraph — it sends the reader somewhere that
does not exist and looks like the map is right. Renaming a file breaks these
links with no other signal anywhere in the project.
"""

import re
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parents[3]

IGNORED_DIRS = {
    ".git",
    ".venv",
    ".pytest_cache",
    "node_modules",
    "staticfiles",
    "static",
    "var",
    "htmlcov",
}

# [text](target) — skipping external links, anchors and mailto:
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def markdown_files() -> list[Path]:
    return [
        path
        for path in BASE_DIR.rglob("*.md")
        if not IGNORED_DIRS & set(path.relative_to(BASE_DIR).parts)
    ]


def relative_links(path: Path) -> list[str]:
    links = []
    for target in LINK_RE.findall(path.read_text(encoding="utf-8")):
        target = target.split(" ")[0].split("#")[0].strip()
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        links.append(target)
    return links


def test_markdown_files_are_found():
    assert markdown_files()


@pytest.mark.parametrize("path", markdown_files(), ids=lambda p: str(p.relative_to(BASE_DIR)))
def test_relative_links_resolve(path):
    broken = [target for target in relative_links(path) if not (path.parent / target).exists()]
    assert not broken, f"{path.relative_to(BASE_DIR)} links to missing paths: {broken}"


@pytest.mark.parametrize("path", markdown_files(), ids=lambda p: str(p.relative_to(BASE_DIR)))
def test_referenced_make_targets_exist(path):
    """`make something` in the docs has to be a target the Makefile actually has."""
    makefile = (BASE_DIR / "Makefile").read_text(encoding="utf-8")
    targets = set(re.findall(r"^([a-zA-Z0-9_-]+):", makefile, flags=re.MULTILINE))

    referenced = set(re.findall(r"`make ([a-zA-Z0-9_-]+)", path.read_text(encoding="utf-8")))
    missing = referenced - targets

    assert not missing, f"{path.relative_to(BASE_DIR)} mentions unknown make targets: {missing}"
