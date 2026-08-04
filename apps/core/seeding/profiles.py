"""
Volume profiles for demo data.

A profile is a multiplier plus a set of "how many of what". A seeder never
hardcodes counts: it asks ``ctx.count("users")`` and the same code produces 5
records under ``tiny`` and 480 under ``large``.

Add your own keys to ``_BASE_COUNTS`` as you add seeders — a missing key is not
an error, ``count()`` just returns the default you pass.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SeedProfile:
    """A named set of counts for generating demo data."""

    name: str
    description: str
    counts: dict[str, int] = field(default_factory=dict)

    def count(self, key: str, default: int = 0) -> int:
        return self.counts.get(key, default)


# Baseline counts (the `small` profile). Other profiles scale them, except keys
# listed in `_ABSOLUTE` — those describe structure, not volume.
_BASE_COUNTS: dict[str, int] = {
    "users": 24,
}

_ABSOLUTE: frozenset[str] = frozenset()

_MULTIPLIERS: dict[str, tuple[float, str]] = {
    "tiny": (0.2, "Bare minimum for a smoke test — seeds in a second"),
    "small": (1.0, "Default: every scenario covered, data still readable"),
    "medium": (5.0, "Pagination, filters, list-page load"),
    "large": (20.0, "Query profiling and N+1 hunting at realistic volumes"),
}


def _build(name: str) -> SeedProfile:
    multiplier, description = _MULTIPLIERS[name]
    counts = {
        key: value if key in _ABSOLUTE else max(1, round(value * multiplier))
        for key, value in _BASE_COUNTS.items()
    }
    return SeedProfile(name=name, description=description, counts=counts)


PROFILES: dict[str, SeedProfile] = {name: _build(name) for name in _MULTIPLIERS}

DEFAULT_PROFILE = "small"


def get_profile(name: str) -> SeedProfile:
    try:
        return PROFILES[name]
    except KeyError:
        raise ValueError(
            f"Unknown profile {name!r}. Available: {', '.join(sorted(PROFILES))}"
        ) from None
