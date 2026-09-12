import json
import logging
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)


def notify_new_request(request_obj):
    """Best-effort ping to Slack when a new request comes in.

    Never raises — a notification failure should not block the guest-facing
    request flow. No-ops silently if SLACK_WEBHOOK_URL isn't configured.
    """
    webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', '')
    if not webhook_url:
        return

    lines = [
        f"*New request:* {request_obj.get_request_type_display()}",
        f"*Name:* {request_obj.guest_name or '—'}",
        f"*Email:* {request_obj.email or '—'}",
        f"*Company:* {request_obj.organization or '—'}",
    ]
    for key, value in (request_obj.details or {}).items():
        lines.append(f"*{key.replace('_', ' ').title()}:* {value}")

    payload = {"text": "\n".join(lines)}

    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        logger.exception("Failed to send Slack notification for request %s", request_obj.id)
