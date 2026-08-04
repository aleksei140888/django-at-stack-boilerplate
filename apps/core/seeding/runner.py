"""Running the seeders: order, transaction boundary, timings."""

from __future__ import annotations

import time

from django.db import transaction

from .context import SeedContext
from .registry import get_seeders


def run_seeders(ctx: SeedContext, *, only: list[str] | None = None) -> SeedContext:
    """Run all (or the selected) seeders inside a single transaction."""
    seeders = get_seeders(only=only)

    with transaction.atomic():
        for seeder in seeders:
            started = time.perf_counter()
            seeder.seed(ctx)
            ctx.log(f"  {seeder.name:<18} {time.perf_counter() - started:6.2f}s")

    return ctx


def clear_demo_data(*, only: list[str] | None = None) -> dict[str, int]:
    """
    Delete demo data in reverse registration order.

    Reverse order matters as soon as one domain protects another with
    ``on_delete=PROTECT``: deleting the provider first raises instead of
    cascading. Each ``clear`` only removes rows carrying the demo marker, so the
    command is safe to run against a database that also holds real data.
    """
    deleted: dict[str, int] = {}

    with transaction.atomic():
        for seeder in reversed(get_seeders(only=only)):
            if seeder.clear is None:
                continue
            count = seeder.clear()
            if count:
                deleted[seeder.name] = count

    return deleted
