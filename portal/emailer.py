from __future__ import annotations

import json
import os
import urllib.request
import urllib.error


BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_email(*, subject: str, body: str, to_email: str, from_email: str | None = None) -> None:
    """
    Send email via Brevo (HTTPS API) so it works on Render even when SMTP is blocked.
    """
    api_key = os.environ.get("BREVO_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("BREVO_API_KEY is not set")

    sender = (from_email or os.environ.get("DEFAULT_FROM_EMAIL", "")).strip()
    if not sender:
        raise RuntimeError("DEFAULT_FROM_EMAIL is not set")

    # Brevo expects sender as {"name": "...", "email": "..."}.
    # Accept either "Name <email@x.com>" or "email@x.com"
    name = None
    email = sender

    if "<" in sender and ">" in sender:
        name = sender.split("<", 1)[0].strip().strip('"')
        email = sender.split("<", 1)[1].split(">", 1)[0].strip()

    payload = {
        "sender": {"email": email, **({"name": name} if name else {})},
        "to": [{"email": to_email}],
        "subject": subject,
        "textContent": body,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BREVO_API_URL,
        data=data,
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            # Consume response (optional)
            resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Brevo HTTPError {e.code}: {detail}") from e
    except Exception as e:
        raise RuntimeError(f"Brevo send failed: {e}") from e
