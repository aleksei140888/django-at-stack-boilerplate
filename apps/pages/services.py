"""
Side effects for the pages app.

Sending mail is a side effect, so it lives here rather than in the view — same
rule as database writes (docs/architecture.md). It also means the delivery
failure path is written down once instead of per call site.
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_contact_message(*, name: str, email: str, message: str) -> bool:
    """
    Deliver a contact form submission. Returns whether it was sent.

    Failures are logged and swallowed: the visitor cannot fix a broken SMTP
    connection, and a 500 on the contact page tells them nothing useful. The log
    line is what makes the drop visible — silently returning success is what the
    previous `fail_silently=True` did, with nothing recorded anywhere.
    """
    try:
        send_mail(
            subject=f"Contact from {name}",
            message=f"From: {name} <{email}>\n\n{message}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.CONTACT_EMAIL],
            fail_silently=False,
        )
        return True
    except Exception as exc:
        logger.error(
            "contact form delivery failed",
            extra={"error": f"{type(exc).__name__}: {exc}", "sender": email},
        )
        return False
