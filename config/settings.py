import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)

def send_email(subject: str, to_email: str, text_body: str, html_body: str | None = None) -> None:
    """
    Sends email using Django's configured email backend.
    Uses DEFAULT_FROM_EMAIL if set, otherwise falls back to EMAIL_HOST_USER.
    Raises exception so Render logs show the real failure.
    """
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", None)

    if not from_email:
        raise RuntimeError("Email not configured: DEFAULT_FROM_EMAIL or EMAIL_HOST_USER missing.")

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=[to_email],
    )

    if html_body:
        msg.attach_alternative(html_body, "text/html")

    try:
        msg.send(fail_silently=False)
        logger.info("Email sent to=%s subject=%s", to_email, subject)
    except Exception as e:
        logger.exception("Email send failed to=%s subject=%s error=%s", to_email, subject, e)
        raise
