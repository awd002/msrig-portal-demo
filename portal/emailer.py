import os
import requests


def send_email(subject: str, body: str, to_email: str) -> bool:
    """
    Send email via Brevo (Sendinblue) API over HTTPS.
    Returns True if accepted, False otherwise. Never raises.
    """
    api_key = (os.environ.get("BREVO_API_KEY") or "").strip()
    from_email = (os.environ.get("DEFAULT_FROM_EMAIL") or "msrig.portal@gmail.com").strip()
    from_name = (os.environ.get("DEFAULT_FROM_NAME") or "MSRIG Portal").strip()

    # If not configured, do nothing (but don't crash).
    if not api_key:
        return False

    try:
        r = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "api-key": api_key,
                "content-type": "application/json",
            },
            json={
                "sender": {"name": from_name, "email": from_email},
                "to": [{"email": to_email}],
                "subject": subject,
                "textContent": body,
            },
            timeout=10,
        )
        return 200 <= r.status_code < 300
    except Exception:
        return False
