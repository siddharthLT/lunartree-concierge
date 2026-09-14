import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .models import ConciergeRequest
from .notifications import notify_new_request

VALID_TYPES = {choice[0] for choice in ConciergeRequest.TYPE_CHOICES}


def landing(request):
    return render(request, 'concierge/landing.html')


def ddf_intel(request):
    return render(request, 'concierge/ddf_intel.html')


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
