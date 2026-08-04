import pytest

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.core.seeding import SeedContext, get_profile, seeder_registry
from apps.core.seeding.context import DEMO_EMAIL_DOMAIN
from apps.core.seeding.profiles import PROFILES
from apps.core.seeding.registry import Seeder, register_seeder
from apps.core.seeding.runner import clear_demo_data, run_seeders

User = get_user_model()


@pytest.fixture
def isolated_registry():
    """
    Swap in an empty registry for the test and restore the real one after.

    The registry is module-level state, so without this the fake seeders below
    would leak into every later test on the same xdist worker (docs/testing.md).
    """
    saved_seeders = dict(seeder_registry._seeders)
    saved_discovered = seeder_registry._discovered
    seeder_registry._seeders.clear()
    seeder_registry._discovered = True  # skip autodiscovery of the real ones
    yield seeder_registry
    seeder_registry._seeders.clear()
    seeder_registry._seeders.update(saved_seeders)
    seeder_registry._discovered = saved_discovered


def context(profile="small") -> SeedContext:
    return SeedContext.create(profile=get_profile(profile), seed=1)


class TestProfiles:
    def test_every_profile_scales_the_same_keys(self):
        key_sets = {frozenset(profile.counts) for profile in PROFILES.values()}
        assert len(key_sets) == 1

    def test_larger_profile_means_more_data(self):
        assert PROFILES["tiny"].count("users") < PROFILES["large"].count("users")

    def test_counts_never_reach_zero(self):
        # A zero would make the tiny profile seed nothing at all and pass anyway.
        assert all(value >= 1 for value in PROFILES["tiny"].counts.values())

    def test_unknown_profile_is_rejected_by_name(self):
        with pytest.raises(ValueError, match="huge"):
            get_profile("huge")


class TestContext:
    def test_same_seed_gives_the_same_data(self):
        first = [context().pick("abcdef") for _ in range(10)]
        second = [context().pick("abcdef") for _ in range(10)]
        assert first == second

    def test_past_is_in_the_past(self):
        ctx = context()
        assert ctx.past(30) < ctx.now

    def test_future_is_in_the_future(self):
        ctx = context()
        assert ctx.future(30) > ctx.now

    def test_sample_never_exceeds_the_population(self):
        assert len(context().sample([1, 2, 3], 10)) == 3

    def test_require_names_the_missing_key(self):
        with pytest.raises(KeyError, match="users"):
            context().require("users")

    def test_record_counts_towards_the_report(self):
        ctx = context()
        ctx.record("things", [1, 2, 3])
        assert ctx.result.created["things"] == 3
        assert ctx.result.total == 3


@pytest.mark.django_db
class TestRegistry:
    """run_seeders/clear_demo_data wrap everything in a transaction, so these
    need a database even though the fake seeders touch no models."""

    def test_seeders_run_in_order(self, isolated_registry):
        calls = []

        @register_seeder("second", order=20)
        def _second(ctx):
            calls.append("second")

        @register_seeder("first", order=10)
        def _first(ctx):
            calls.append("first")

        run_seeders(context())
        assert calls == ["first", "second"]

    def test_only_runs_the_selected_seeders(self, isolated_registry):
        calls = []
        register_seeder("a", order=10)(lambda ctx: calls.append("a"))
        register_seeder("b", order=20)(lambda ctx: calls.append("b"))

        run_seeders(context(), only=["b"])
        assert calls == ["b"]

    def test_unknown_seeder_name_lists_the_real_ones(self, isolated_registry):
        register_seeder("a", order=10)(lambda ctx: None)

        with pytest.raises(ValueError, match="Available: a"):
            run_seeders(context(), only=["nope"])

    # Reverse order matters as soon as one domain PROTECTs another: deleting the
    # provider first raises instead of cascading.
    def test_clear_runs_in_reverse_order(self, isolated_registry):
        cleared = []
        isolated_registry.register(
            Seeder("first", 10, lambda ctx: None, clear=lambda: cleared.append("first") or 1)
        )
        isolated_registry.register(
            Seeder("second", 20, lambda ctx: None, clear=lambda: cleared.append("second") or 1)
        )

        clear_demo_data()
        assert cleared == ["second", "first"]

    def test_seeders_without_a_clear_are_skipped(self, isolated_registry):
        register_seeder("a", order=10)(lambda ctx: None)
        assert clear_demo_data() == {}


@pytest.mark.django_db
class TestAccountsSeeder:
    def test_creates_named_accounts_and_a_user_pool(self):
        call_command("seed_demo", "--profile=tiny", "--quiet", "--force")

        demo_users = User.objects.filter(email__endswith=f"@{DEMO_EMAIL_DOMAIN}")
        assert demo_users.filter(email=f"admin@{DEMO_EMAIL_DOMAIN}", is_superuser=True).exists()
        assert demo_users.count() > len(["admin", "moderator", "user"])

    def test_demo_users_can_actually_log_in(self, client):
        call_command("seed_demo", "--profile=tiny", "--quiet", "--force")

        logged_in = client.login(email=f"user@{DEMO_EMAIL_DOMAIN}", password="demo12345")
        assert logged_in

    def test_running_twice_does_not_duplicate(self):
        call_command("seed_demo", "--profile=tiny", "--quiet", "--force")
        before = User.objects.count()
        call_command("seed_demo", "--profile=tiny", "--quiet", "--force")

        assert User.objects.count() == before

    def test_clear_removes_only_demo_users(self):
        real_user = User.objects.create_user(email="real@example.com", password="x")
        call_command("seed_demo", "--profile=tiny", "--quiet", "--force")

        call_command("seed_demo", "--clear", "--force")

        assert User.objects.filter(pk=real_user.pk).exists()
        assert not User.objects.filter(email__endswith=f"@{DEMO_EMAIL_DOMAIN}").exists()

    # Seeding a production database is not recoverable, so DEBUG=False is treated
    # as "this might be production" unless the caller insists.
    def test_refuses_to_run_with_debug_off(self, settings):
        settings.DEBUG = False

        with pytest.raises(CommandError, match="--force"):
            call_command("seed_demo", "--profile=tiny", "--quiet")
