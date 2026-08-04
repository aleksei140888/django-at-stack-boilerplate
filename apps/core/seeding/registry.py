"""The seeder registry: apps register themselves, core only finds them."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .context import SeedContext

SeedFn = Callable[[SeedContext], None]
ClearFn = Callable[[], int]


@dataclass(frozen=True)
class Seeder:
    """One registered domain seeder."""

    name: str
    order: int
    seed: SeedFn
    clear: ClearFn | None = None
    description: str = ""


class SeederRegistry:
    """A plain dict registry (KISS) with a deterministic execution order."""

    def __init__(self) -> None:
        self._seeders: dict[str, Seeder] = {}
        self._discovered = False

    def register(self, seeder: Seeder) -> None:
        self._seeders[seeder.name] = seeder

    def autodiscover(self) -> None:
        """Import every installed app's ``seeding.py`` (once per process)."""
        if self._discovered:
            return
        from django.utils.module_loading import autodiscover_modules

        autodiscover_modules("seeding")
        self._discovered = True

    def all(self, *, only: list[str] | None = None) -> list[Seeder]:
        self.autodiscover()
        seeders = sorted(self._seeders.values(), key=lambda s: (s.order, s.name))
        if only:
            unknown = set(only) - {s.name for s in seeders}
            if unknown:
                raise ValueError(
                    f"Unknown seeders: {', '.join(sorted(unknown))}. "
                    f"Available: {', '.join(s.name for s in seeders)}"
                )
            seeders = [s for s in seeders if s.name in only]
        return seeders

    def clear(self) -> None:
        """Reset the registry — needed by tests that register fake seeders."""
        self._seeders.clear()
        self._discovered = False


seeder_registry = SeederRegistry()


def register_seeder(
    name: str,
    *,
    order: int = 100,
    clear: ClearFn | None = None,
    description: str = "",
) -> Callable[[SeedFn], SeedFn]:
    """
    Register a domain seeder.

    Use it in your app's ``seeding.py``::

        @register_seeder("articles", order=40, clear=clear_demo_articles)
        def seed_articles(ctx: SeedContext) -> None:
            ...

    ``order`` decides the sequence, lowest first. A seeder that reads another
    domain's objects from ``ctx.store`` needs a higher ``order`` than the one
    that puts them there. ``clear`` is called by ``--fresh`` in reverse order and
    returns how many rows it deleted.
    """

    def decorator(fn: SeedFn) -> SeedFn:
        seeder_registry.register(
            Seeder(
                name=name,
                order=order,
                seed=fn,
                clear=clear,
                description=description or (fn.__doc__ or "").strip().split("\n")[0],
            )
        )
        return fn

    return decorator


def get_seeders(*, only: list[str] | None = None) -> list[Seeder]:
    return seeder_registry.all(only=only)
