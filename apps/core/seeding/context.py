"""State shared by one seeding run."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Iterable, Sequence, TypeVar

from django.utils import timezone

from .profiles import SeedProfile

T = TypeVar("T")

# Marker for demo data. Everything a seeder creates must be findable by it —
# otherwise `--fresh` cannot delete demo data without touching real records.
DEMO_MARKER = "demo"

#: Demo user emails: ``<name>@demo.local``.
DEMO_EMAIL_DOMAIN = "demo.local"

#: Slug prefix for demo content.
DEMO_SLUG_PREFIX = "demo-"


@dataclass
class SeedResult:
    """How many objects each seeder created (for the command's report)."""

    created: dict[str, int] = field(default_factory=dict)

    def add(self, label: str, count: int) -> None:
        if count:
            self.created[label] = self.created.get(label, 0) + count

    @property
    def total(self) -> int:
        return sum(self.created.values())


def _noop(message: str) -> None:
    """Default logger — seeders call ctx.log() unconditionally."""


@dataclass
class SeedContext:
    """
    Shared run state: deterministic RNG, volume profile, clock and a store.

    ``store`` is the only channel between seeders of different apps: one puts the
    objects it created there, later ones read them. There are no direct imports
    between the ``seeding.py`` modules of different apps, so an app can be
    removed from the project without breaking the rest of the seeding chain.
    """

    profile: SeedProfile
    rng: random.Random
    now: datetime
    result: SeedResult = field(default_factory=SeedResult)
    store: dict[str, Any] = field(default_factory=dict)
    log: Callable[[str], None] = _noop

    @classmethod
    def create(cls, profile: SeedProfile, seed: int, log: Callable[[str], None] | None = None):
        return cls(
            profile=profile,
            rng=random.Random(seed),
            now=timezone.now(),
            log=log or _noop,
        )

    # -- Volumes --

    def count(self, key: str, default: int = 0) -> int:
        return self.profile.count(key, default)

    # -- Randomness (deterministic for a given --seed) --

    def pick(self, items: Sequence[T]) -> T:
        return items[self.rng.randrange(len(items))]

    def sample(self, items: Sequence[T], k: int) -> list[T]:
        k = min(k, len(items))
        return self.rng.sample(list(items), k) if k else []

    def chance(self, probability: float) -> bool:
        return self.rng.random() < probability

    def past(self, max_days: int = 180, min_days: int = 0) -> datetime:
        """A moment in the past, uniform within [min_days, max_days]."""
        days = self.rng.randint(min_days, max_days)
        seconds = self.rng.randrange(24 * 3600)
        return self.now - timedelta(days=days, seconds=seconds)

    def future(self, max_days: int = 60, min_days: int = 1) -> datetime:
        days = self.rng.randint(min_days, max_days)
        return self.now + timedelta(days=days, seconds=self.rng.randrange(24 * 3600))

    # -- Shared store --

    def put(self, key: str, value: Any) -> Any:
        self.store[key] = value
        return value

    def get(self, key: str, default: Any = None) -> Any:
        return self.store.get(key, default)

    def require(self, key: str) -> Any:
        """Data a seeder cannot run without (e.g. users for comments)."""
        if key not in self.store:
            raise KeyError(
                f"{key!r} is not in the shared store — check the seeder's `order`: "
                "whatever provides it has to run earlier."
            )
        return self.store[key]

    # -- Report --

    def record(self, label: str, objects: Iterable[Any]) -> list[Any]:
        items = list(objects)
        self.result.add(label, len(items))
        return items
