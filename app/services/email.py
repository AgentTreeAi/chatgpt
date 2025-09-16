"""Email delivery helpers."""
from __future__ import annotations

import logging
from typing import Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def send_magic_link(to_email: str, link: str, template_id: Optional[str] = None) -> None:
    """Send a passwordless login link via SendGrid."""

    settings = get_settings()
    if not settings.sendgrid_api_key:
        logger.warning("SENDGRID_API_KEY not set; magic link logged instead")
        logger.info("Magic link for %s: %s", to_email, link)
        return

    message = Mail(from_email="no-reply@rmht.app", to_emails=to_email)
    if template_id:
        message.template_id = template_id
        message.dynamic_template_data = {"magic_link": link}
    else:
        message.subject = "Your RMHT magic link"
        message.html_content = f"<p>Click to sign in: <a href='{link}'>{link}</a></p>"

    try:
        client = SendGridAPIClient(settings.sendgrid_api_key)
        client.send(message)
    except Exception:  # pragma: no cover
        logger.exception("Failed to send magic link email")
