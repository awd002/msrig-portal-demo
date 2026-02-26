from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail


def send_email(*, subject: str, body: str, to_email: str, from_email: str | None = None) -> None:
    """
    Thin wrapper around Django's email system.

    Uses settings.EMAIL_BACKEND, settings.DEFAULT_FROM_EMAIL, and your SMTP env vars.
    """
    if not to_email:
        return

    send_mail(
        subject=subject,
        message=body,
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )
