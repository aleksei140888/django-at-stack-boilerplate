"""
Demo seeding: generate a realistic dataset for the demo environment.

Each app owns its own ``seeding.py`` and registers a seeder with the
``@register_seeder`` decorator — core knows nothing about the domains up front
(autodiscovery, the same pattern Django uses for ``admin.py``). Execution order
is set by ``order``.

Seeders only ever touch data carrying the demo marker (:data:`DEMO_MARKER`), so
``--fresh`` can never delete real records. That constraint is what makes it safe
to run the seeder against a database that already has real content in it.

Adding a seeder for your own app: docs/playbooks/add-seeder.md
"""

from .context import DEMO_EMAIL_DOMAIN, DEMO_MARKER, SeedContext, SeedResult
from .profiles import PROFILES, SeedProfile, get_profile
from .registry import get_seeders, register_seeder, seeder_registry
from .runner import clear_demo_data, run_seeders

__all__ = [
    "DEMO_EMAIL_DOMAIN",
    "DEMO_MARKER",
    "PROFILES",
    "SeedContext",
    "SeedProfile",
    "SeedResult",
    "clear_demo_data",
    "get_profile",
    "get_seeders",
    "register_seeder",
    "run_seeders",
    "seeder_registry",
]
