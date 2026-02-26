import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


def send_email(subject: str, to_email: str, text_body: str, html_body: str | None = None) -> None:
    """
    Sends email using Django's configured email backend.
    Respects settings.EMAIL_BACKEND (console or smtp).
    """

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)

    if not from_email:
        raise RuntimeError("DEFAULT_FROM_EMAIL not configured.")

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=[to_email],
    )

    if html_body:
        message.attach_alternative(html_body, "text/html")

    try:
        message.send(fail_silently=False)
        logger.info("Email sent to %s | subject=%s", to_email, subject)
    except Exception as e:
        logger.exception("Email failed to %s | subject=%s | error=%s", to_email, subject, e)
        raise
