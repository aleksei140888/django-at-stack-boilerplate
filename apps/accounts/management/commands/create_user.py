"""Create a regular user without an interactive prompt (CI, provisioning, demos)."""

from django.core.management.base import BaseCommand, CommandError

from apps.accounts import selectors, services


class Command(BaseCommand):
    help = "Create a regular user (non-interactive)"

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="User email")
        parser.add_argument("--password", required=True, help="User password")
        parser.add_argument("--first-name", default="", help="First name")
        parser.add_argument("--last-name", default="", help="Last name")

    def handle(self, *args, **options):
        email = options["email"]

        if selectors.get_user_by_email(email):
            raise CommandError(f"User with email '{email}' already exists.")

        user = services.register_user(
            email=email,
            password=options["password"],
            first_name=options["first_name"],
            last_name=options["last_name"],
        )
        self.stdout.write(self.style.SUCCESS(f"User created: {user.email}"))
