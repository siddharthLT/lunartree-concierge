import json
import secrets

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from django.conf import settings
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.csrf import ensure_csrf_cookie

from . import directory, recs
from .models import ConciergeRequest, Visitor
from .notifications import email_new_request, notify_new_request

VALID_TYPES = {choice[0] for choice in ConciergeRequest.TYPE_CHOICES}


VISITOR_COOKIE = 'cl_visitor'
VISITOR_COOKIE_AGE = 60 * 60 * 24 * 400  # browsers cap cookie lifetime at ~400 days

MODALITIES = {'api', 'adc', 'cell', 'gene', 'editing', 'mab', 'protein', 'bispecific',
              'digital', 'microbiome', 'radio', 'small', 'device', 'biosimilar'}
PHASES = {'discovery', 'preclinical', 'phase1', 'phase2', 'phase3', 'commercial'}
GEOGRAPHIES = {'nam', 'eu', 'apac', 'mea', 'anz'}


def _current_visitor(request):
    token = request.COOKIES.get(VISITOR_COOKIE)
    return Visitor.objects.filter(token=token).first() if token else None


def _set_visitor_cookie(response, token):
    response.set_cookie(VISITOR_COOKIE, token, max_age=VISITOR_COOKIE_AGE,
                        httponly=True, samesite='Lax', secure=not settings.DEBUG)


def landing(request):
    visitor = _current_visitor(request)
    if not (visitor and visitor.completed) and 'skip' not in request.GET:
        return redirect('concierge:welcome')
    known = visitor if visitor and visitor.completed else None
    return render(request, 'concierge/landing.html', {
        'visitor': known,
        'recs': recs.for_visitor(known) if known else None,
        'profile': {'modalities': known.modalities, 'phases': known.phases, 'geographies': known.geographies} if known else None,
    })


@ensure_csrf_cookie
def welcome(request):
    visitor = _current_visitor(request)
    if visitor and visitor.completed and 'switch' not in request.GET:
        return redirect('concierge:landing')
    account_setup = {'url': settings.ACCOUNT_SETUP_API_URL, 'siteKey': settings.TURNSTILE_SITE_KEY, 'appearance': settings.TURNSTILE_APPEARANCE} if settings.ACCOUNT_SETUP_API_URL else None
    return render(request, 'concierge/welcome.html', {'account_setup': account_setup})


def welcome_search(request):
    return JsonResponse({'results': directory.search(request.GET.get('q', ''))})


def welcome_person(request, pid):
    person = directory.person_detail(pid)
    if not person:
        return JsonResponse({'ok': False}, status=404)
    return JsonResponse({'ok': True, 'person': person})


def attendees_api(request):
    visitor = _current_visitor(request)
    if not (visitor and visitor.completed):
        return JsonResponse({'ok': False}, status=403)
    return JsonResponse({'ok': True, 'people': directory.attendees(), 'labels': recs.MODALITY_TITLE})


def _clean_list(values, allowed):
    return [v for v in (values or []) if v in allowed] if isinstance(values, list) else []


@require_POST
def welcome_save(request):
    """Upsert the visitor. Called after each answered step so a half-finished
    flow still leaves us with who they are; `completed` flips on the last one."""
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON.'}, status=400)

    visitor = None if payload.get('fresh') else _current_visitor(request)
    if not visitor:
        visitor = Visitor(token=secrets.token_urlsafe(32))
    visitor.user_agent = request.META.get('HTTP_USER_AGENT', '')[:300]

    def text(key, limit):
        return str(payload.get(key) or '').strip()[:limit]

    if 'name' in payload:
        visitor.name = text('name', 200)
        visitor.title = text('title', 300)
        visitor.company = text('company', 200)
        visitor.company_domain = text('company_domain', 200).lower()
        visitor.segment = text('segment', 40)
        visitor.directory_id = text('directory_id', 40)
    if payload.get('use_directory_email') and visitor.directory_id:
        visitor.email = directory.person_email(visitor.directory_id)
    elif text('email', 254):
        try:
            validate_email(text('email', 254))
            visitor.email = text('email', 254).lower()
        except ValidationError:
            return JsonResponse({'ok': False, 'error': 'Invalid email.'}, status=400)
    if 'modalities' in payload:
        visitor.modalities = _clean_list(payload['modalities'], MODALITIES)
    if 'phases' in payload:
        visitor.phases = _clean_list(payload['phases'], PHASES)
    if 'geographies' in payload:
        visitor.geographies = _clean_list(payload['geographies'], GEOGRAPHIES)
    if 'strengths' in payload:
        visitor.strengths = text('strengths', 1000)
    if 'exclusions' in payload:
        visitor.exclusions = text('exclusions', 1000)
    if payload.get('completed'):
        visitor.completed = True
    visitor.save()

    response = JsonResponse({'ok': True, 'token': visitor.token, 'first_name': visitor.first_name})
    _set_visitor_cookie(response, visitor.token)
    return response


@require_POST
def welcome_restore(request):
    """Re-issue the cookie from the localStorage mirror when it has expired or
    been cleared (e.g. Safari's tracking prevention)."""
    try:
        token = json.loads(request.body).get('token', '')
    except json.JSONDecodeError:
        token = ''
    visitor = Visitor.objects.filter(token=token).first() if token else None
    if not visitor:
        return JsonResponse({'ok': False}, status=404)
    response = JsonResponse({'ok': True, 'completed': visitor.completed})
    _set_visitor_cookie(response, visitor.token)
    return response


def ddf_intel(request):
    return render(request, 'concierge/ddf_intel.html')


@xframe_options_sameorigin  # the Experience tab embeds this page
def experience_biolens(request):
    return render(request, 'concierge/experience_biolens.html')


@require_POST
def submit_request(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON.'}, status=400)

    request_type = payload.get('type')
    if request_type not in VALID_TYPES:
        return JsonResponse({'ok': False, 'error': 'Unknown request type.'}, status=400)

    obj = ConciergeRequest.objects.create(
        request_type=request_type,
        guest_name=payload.get('guest_name', '') or '',
        email=payload.get('email', '') or '',
        organization=payload.get('organization', '') or '',
        role=payload.get('role', '') or '',
        details=payload.get('details') or {},
    )
    notify_new_request(obj)
    return JsonResponse({'ok': True, 'id': obj.id})


@require_POST
def search_interest(request):
    """A visitor tapped one of their ICP searches (or typed their own). Stored as
    a request and emailed to NOTIFY_EMAIL."""
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON.'}, status=400)
    term = str(payload.get('term') or '').strip()[:300]
    if not term:
        return JsonResponse({'ok': False, 'error': 'Empty search.'}, status=400)

    visitor = _current_visitor(request)
    details = {
        'search': term,
        'source': 'typed' if payload.get('other') else 'suggested',
    }
    if visitor:
        details.update({
            'modalities': ', '.join(visitor.modalities),
            'programs': ', '.join(visitor.phases),
            'geographies': ', '.join(visitor.geographies),
        })
    obj = ConciergeRequest.objects.create(
        request_type=ConciergeRequest.SEARCH_INTEREST,
        guest_name=visitor.name if visitor else '',
        email=visitor.email if visitor else '',
        organization=visitor.company if visitor else '',
        role=(visitor.title if visitor else '')[:50],
        details=details,
    )
    notify_new_request(obj)
    email_new_request(obj)
    return JsonResponse({'ok': True, 'id': obj.id})
