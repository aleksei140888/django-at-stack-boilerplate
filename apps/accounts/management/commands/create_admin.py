"""
Create a superuser without an interactive prompt.

`createsuperuser` needs a TTY, which CI jobs, provisioning playbooks and agent
sessions do not have; `--noinput` there requires the password in an env var and
still skips the role field this project keeps on the user model.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.accounts import selectors

User = get_user_model()


class Command(BaseCommand):
    help = "Create an admin superuser (non-interactive)"

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="Admin email")
        parser.add_argument("--password", required=True, help="Admin password")
        parser.add_argument("--first-name", default="", help="First name")
        parser.add_argument("--last-name", default="", help="Last name")

    def handle(self, *args, **options):
        email = options["email"]

        if selectors.get_user_by_email(email):
            raise CommandError(f"User with email '{email}' already exists.")

        user = User.objects.create_superuser(
            email=email,
            password=options["password"],
            first_name=options["first_name"],
            last_name=options["last_name"],
            role=User.Role.ADMIN,
            gdpr_consent=True,
            gdpr_consent_date=timezone.now(),
        )
        self.stdout.write(self.style.SUCCESS(f"Admin created: {user.email}"))
