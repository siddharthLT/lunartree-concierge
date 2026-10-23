"""Server-side BioLens account request (POST {ACCOUNT_SETUP_API_URL}/account-setup/requests).

The browser only forwards the Turnstile token it solved; the payload is built here from the
saved Visitor, and the backend's answer is logged instead of being lost to a page redirect.
"""
import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

# Slower than the old 8s browser timeout: the backend verifies the token and notifies reviewers inline.
TIMEOUT = 30

FREE_MAIL = {'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'icloud.com', 'aol.com',
             'proton.me', 'protonmail.com', 'live.com', 'msn.com', 'me.com'}


def build_payload(visitor, turnstile_token):
    """None when the visitor can't be turned into a valid request."""
    email = visitor.email
    domain = visitor.company_domain
    if not domain and email and email.split('@')[-1].lower() not in FREE_MAIL:
        domain = email.split('@')[-1].lower()
    if not (visitor.name and email and visitor.company and len(domain) >= 3):
        return None
    return {
        'name': visitor.name[:100], 'email': email, 'company': visitor.company[:200], 'company_domain': domain[:255],
        'title': visitor.title[:200], 'segment': visitor.segment[:100],
        'modalities': ['Other: ' + m[6:] if m.startswith('other:') else m for m in visitor.modalities],
        'phases': visitor.phases, 'geographies': visitor.geographies,
        'strengths': visitor.strengths[:2000], 'exclusions': visitor.exclusions[:2000],
        'directory_id': visitor.directory_id[:100], 'completed': visitor.completed,
        'user_agent': visitor.user_agent[:1000],
        'created_at': visitor.created_at.isoformat(), 'updated_at': visitor.updated_at.isoformat(),
        'cf_turnstile_token': turnstile_token,
    }


def send(payload):
    """(status, body) from the backend; status 0 and the error text when it couldn't be reached."""
    req = urllib.request.Request(
        f'{settings.ACCOUNT_SETUP_API_URL}/account-setup/requests',
        data=json.dumps(payload).encode(), method='POST',
        headers={'Content-Type': 'application/json', 'User-Agent': 'lunartree-concierge/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
            status, body = res.status, res.read(2000).decode('utf-8', 'replace')
    except urllib.error.HTTPError as err:
        status, body = err.code, err.read(2000).decode('utf-8', 'replace')
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        status, body = 0, f'{type(err).__name__}: {err}'
    # Never log the token or the person's details, just the outcome.
    log = logger.info if status == 202 else logger.warning
    log('account request for visitor email domain %s: %s %s', payload['email'].split('@')[-1], status, body[:300])
    return status, body
