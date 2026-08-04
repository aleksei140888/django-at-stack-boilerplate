"""Fill the demo environment with data."""

from __future__ import annotations

import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.core.seeding import SeedContext, clear_demo_data, get_seeders, run_seeders
from apps.core.seeding.profiles import DEFAULT_PROFILE, PROFILES, get_profile


class Command(BaseCommand):
    help = (
        "Fill the database with demo data. Only creates records carrying the demo "
        "marker, so real data is never touched."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--profile",
            default=DEFAULT_PROFILE,
            choices=sorted(PROFILES),
            help="How much data to create (default: %(default)s)",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=20260804,
            help="RNG seed — the same seed produces the same data",
        )
        parser.add_argument(
            "--fresh",
            action="store_true",
            help="Delete existing demo data first, then seed from scratch",
        )
        parser.add_argument("--clear", action="store_true", help="Only delete demo data")
        parser.add_argument(
            "--only",
            default="",
            help="Comma-separated seeder names (e.g. accounts)",
        )
        parser.add_argument("--list", action="store_true", help="List the seeders and exit")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Allow running with DEBUG=False (refused by default)",
        )
        parser.add_argument("--quiet", action="store_true", help="No per-step output")

    def handle(self, *args, **options):
        only = [name.strip() for name in options["only"].split(",") if name.strip()] or None

        if options["list"]:
            for seeder in get_seeders():
                self.stdout.write(f"  {seeder.order:>3}  {seeder.name:<18} {seeder.description}")
            return

        # DEBUG=False is the closest thing to a "this might be production" signal
        # available here, and seeding a production database is unrecoverable.
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "DEBUG=False — this looks like production. Pass --force if it really is "
                "a demo environment."
            )

        try:
            profile = get_profile(options["profile"])
            seeders = get_seeders(only=only)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        started = time.perf_counter()

        if options["fresh"] or options["clear"]:
            deleted = clear_demo_data(only=only)
            self.stdout.write(f"Demo records deleted: {sum(deleted.values())}")
            if options["clear"]:
                return

        log = (lambda message: None) if options["quiet"] else self.stdout.write
        ctx = SeedContext.create(profile=profile, seed=options["seed"], log=log)

        if not options["quiet"]:
            self.stdout.write(
                f"Profile: {profile.name} ({profile.description}), "
                f"seed: {options['seed']}, seeders: {len(seeders)}"
            )

        run_seeders(ctx, only=only)
        self._print_summary(ctx, time.perf_counter() - started)

    def _print_summary(self, ctx: SeedContext, elapsed: float) -> None:
        if ctx.result.created:
            self.stdout.write("")
            for label, count in sorted(ctx.result.created.items(), key=lambda kv: -kv[1]):
                self.stdout.write(f"  {count:>7}  {label}")

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {ctx.result.total} records in {elapsed:.2f}s "
                f"(profile {ctx.profile.name})"
            )
        )

        from apps.accounts.seeding import DEMO_PASSWORD, NAMED_ACCOUNTS
        from apps.core.seeding.context import DEMO_EMAIL_DOMAIN

        self.stdout.write("")
        self.stdout.write(f"Demo accounts (password for all: {DEMO_PASSWORD}):")
        for username, first_name, last_name, role, _flags in NAMED_ACCOUNTS:
            email = f"{username}@{DEMO_EMAIL_DOMAIN}"
            self.stdout.write(f"  {email:<26} — {first_name} {last_name} ({role})")
