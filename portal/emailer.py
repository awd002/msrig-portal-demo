from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Optional


BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def _parse_sender(sender: str) -> dict:
    """
    Brevo expects sender as {"name": "...", "email": "..."}.
    Accept either "Name <email@x.com>" or "email@x.com".
    """
    sender = (sender or "").strip()
    if not sender:
        raise RuntimeError("DEFAULT_FROM_EMAIL is not set")

    name: Optional[str] = None
    email = sender

    if "<" in sender and ">" in sender:
        name = sender.split("<", 1)[0].strip().strip('"')
        email = sender.split("<", 1)[1].split(">", 1)[0].strip()

    payload = {"email": email}
    if name:
        payload["name"] = name
    return payload


def send_email(
    *,
    subject: str,
    to_email: str,
    text_body: str | None = None,
    html_body: str | None = None,
    # Backwards compatibility: older callers might pass `body=...`
    body: str | None = None,
    from_email: str | None = None,
) -> None:
    """
    Send email via Brevo (HTTPS API) so it works on Render even when SMTP is blocked.

    Preferred args:
      - subject, to_email, text_body (and optionally html_body)

    Backwards compatible:
      - body (treated as text_body if text_body not provided)
    """
    api_key = os.environ.get("BREVO_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("BREVO_API_KEY is not set")

    sender_raw = (from_email or os.environ.get("DEFAULT_FROM_EMAIL", "")).strip()
    sender = _parse_sender(sender_raw)

    # Support legacy `body=` if provided
    if text_body is None and body is not None:
        text_body = body

    # Require at least one body format
    if not text_body and not html_body:
        raise RuntimeError("send_email requires text_body and/or html_body")

    payload: dict = {
        "sender": sender,
        "to": [{"email": to_email}],
        "subject": subject,
    }

    # Brevo supports textContent and htmlContent
    if text_body:
        payload["textContent"] = text_body
    if html_body:
        payload["htmlContent"] = html_body

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
            resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Brevo HTTPError {e.code}: {detail}") from e
    except Exception as e:
        raise RuntimeError(f"Brevo send failed: {e}") from e
