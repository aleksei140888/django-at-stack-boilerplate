"""Helpers shared by seeders."""

from __future__ import annotations

from typing import Sequence

from .context import SeedContext


def backdate(
    ctx: SeedContext, model, objects: Sequence, field: str = "created_at", days: int = 180
) -> None:
    """
    Spread an ``auto_now_add`` field over the past with a single ``bulk_update``.

    ``auto_now_add`` ignores whatever value ``bulk_create`` was given, so the only
    way to get a plausible feed (instead of hundreds of rows sharing one
    timestamp) is to rewrite the column after the insert.
    """
    if not objects:
        return
    for obj in objects:
        setattr(obj, field, ctx.past(days))
    model.objects.bulk_update(objects, [field], batch_size=1000)
