#!/usr/bin/env python
"""
Verify that the project version is identical everywhere it is duplicated.

A drift between `pyproject.toml`, `package.json` and `package-lock.json` used to
surface only in CI — the tagging workflow fails *after* the push to main, when
fixing it costs a separate commit. This script catches the same thing locally,
in pre-commit.

Also enforces the `YYYY.M.PATCH` format (see CLAUDE.md).
"""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

VERSION_RE = re.compile(r"^\d{4}\.\d{1,2}\.\d+$")


def read_versions() -> dict[str, str]:
    versions: dict[str, str] = {}

    with (BASE_DIR / "pyproject.toml").open("rb") as handle:
        versions["pyproject.toml"] = tomllib.load(handle)["project"]["version"]

    package_json = BASE_DIR / "package.json"
    versions["package.json"] = json.loads(package_json.read_text())["version"]

    lock = BASE_DIR / "package-lock.json"
    if lock.exists():
        data = json.loads(lock.read_text())
        versions["package-lock.json"] = data.get("version", "")
        # npm repeats the version inside the root package entry — that is the
        # copy that lags behind, because it only updates on `npm install`.
        root_package = data.get("packages", {}).get("", {})
        if "version" in root_package:
            versions['package-lock.json ("packages" → "")'] = root_package["version"]

    return versions


def main() -> int:
    versions = read_versions()
    unique = set(versions.values())

    if len(unique) > 1:
        print("Project versions disagree:")
        for source, version in versions.items():
            print(f"  {source:<34} {version}")
        print("\nMake them identical (format YYYY.M.PATCH) — auto-tag fails otherwise.")
        return 1

    version = unique.pop()
    if not VERSION_RE.match(version):
        print(f"Version {version!r} does not match the YYYY.M.PATCH format (e.g. 2026.8.0).")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
