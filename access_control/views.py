# access_control/views.py

import json
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import AccessZone, BarcodeAccessLog, PersonalAccessBarcode

logger = logging.getLogger('mediconnect')


@ensure_csrf_cookie
def scanner_page(request):
    """Main scanner page — lists all rooms for selection"""
    zones = AccessZone.objects.filter(is_active=True).order_by('floor_number', 'name')

    # Group zones by floor
    floors = {}
    for zone in zones:
        floor = zone.floor_number
        if floor not in floors:
            floors[floor] = []
        floors[floor].append(zone)

    return render(request, 'access_control/scanner.html', {
        'zones':  zones,
        'floors': dict(sorted(floors.items())),
    })


@csrf_exempt
@require_http_methods(['POST'])
def process_scan(request):
    """
    Core scan processor.
    1. Receives scanned text + selected room
    2. Checks if text matches any zone OR personal badge
    3. Checks role permissions
    4. Logs everything to DB + file
    5. Returns result with sound trigger
    """
    try:
        body = json.loads(request.body)
        scanned_text   = body.get('scanned_text', '').strip()
        barcode_format = body.get('barcode_format', 'unknown')
        selected_room  = body.get('selected_room', '')

        if not scanned_text:
            return JsonResponse({
                'status':  'error',
                'message': 'No barcode data received',
                'sound':   'error',
            }, status=400)

        logger.info(f"Scan received | Text: '{scanned_text}' | Format: {barcode_format}")

        ip     = _get_ip(request)
        device = request.META.get('HTTP_USER_AGENT', '')[:500]

        # ── Resolve user ──────────────────────────────────
        current_user = None
        if request.user.is_authenticated:
            current_user = request.user

        # ── Check 1: Is this a personal staff badge? ──────
        badge = PersonalAccessBarcode.objects.filter(
            barcode_text=scanned_text,
            is_active=True
        ).select_related('user').first()

        if badge:
            if badge.is_expired():
                _log(None, None, scanned_text, barcode_format, 'DENIED', selected_room, ip, device)
                return JsonResponse({
                    'status':  'denied',
                    'reason':  'Staff badge has expired. Contact administration.',
                    'sound':   'denied',
                    'scanned_data': scanned_text,
                })

            current_user = badge.user
            _log(current_user, None, scanned_text, barcode_format, 'GRANTED', selected_room, ip, device)

            return JsonResponse({
                'status':  'granted',
                'message': f'Welcome, {current_user.get_full_name()}!',
                'sound':   'granted',
                'user': {
                    'name':   current_user.get_full_name(),
                    'role':   current_user.role,
                    'email':  current_user.email,
                    'initials': f"{current_user.first_name[:1]}{current_user.last_name[:1]}",
                },
                'access_type':  'personal_badge',
                'scanned_data': scanned_text,
                'barcode_format': barcode_format,
                'timestamp':    timezone.now().strftime('%Y-%m-%d %I:%M:%S %p'),
            })

        # ── Check 2: Is this a zone access code? ──────────
        zone = AccessZone.objects.filter(
            access_code_text=scanned_text,
            is_active=True
        ).first()

        # Partial match fallback
        if not zone and len(scanned_text) >= 5:
            zone = AccessZone.objects.filter(
                access_code_text__icontains=scanned_text[:20],
                is_active=True
            ).first()

        if not zone:
            # Unknown barcode — still log it and show the data
            _log(current_user, None, scanned_text, barcode_format, 'UNKNOWN_CODE', selected_room, ip, device)

            return JsonResponse({
                'status':       'unknown',
                'message':      'Barcode read successfully but not recognized as an access code.',
                'sound':        'scanned',
                'scanned_data': scanned_text,
                'barcode_format': barcode_format,
                'data_display': {
                    'Raw Text':      scanned_text,
                    'Format':        barcode_format,
                    'Length':         f"{len(scanned_text)} characters",
                    'Scanned At':    timezone.now().strftime('%I:%M:%S %p'),
                    'Status':        'Not an access code — Data captured successfully',
                },
                'timestamp': timezone.now().strftime('%Y-%m-%d %I:%M:%S %p'),
            })

        if not zone.is_active:
            _log(current_user, zone, scanned_text, barcode_format, 'INACTIVE_ZONE', selected_room, ip, device)
            return JsonResponse({
                'status': 'denied',
                'reason': f'Zone "{zone.name}" is currently deactivated.',
                'sound':  'denied',
                'scanned_data': scanned_text,
            })

        # ── Check 3: User authentication ──────────────────
        if not current_user:
            _log(None, zone, scanned_text, barcode_format, 'NOT_LOGGED_IN', selected_room, ip, device)
            return JsonResponse({
                'status': 'denied',
                'reason': 'Please log in first to access this zone.',
                'sound':  'denied',
                'scanned_data': scanned_text,
            })

        # ── Check 4: Role authorization ───────────────────
        user_role = current_user.role.upper()
        allowed   = zone.allowed_roles

        if current_user.is_superuser or 'ALL' in [r.upper() for r in allowed]:
            access_granted = True
        else:
            access_granted = user_role in [r.upper() for r in allowed]

        if access_granted:
            _log(current_user, zone, scanned_text, barcode_format, 'GRANTED', selected_room, ip, device)

            return JsonResponse({
                'status':  'granted',
                'message': f'Access Granted – {zone.name}',
                'sound':   'granted',
                'zone': {
                    'name':     zone.name,
                    'type':     zone.get_zone_type_display(),
                    'icon':     zone.get_icon(),
                    'floor':    zone.floor_number,
                    'room':     zone.room_number,
                },
                'user': {
                    'name':     current_user.get_full_name(),
                    'role':     user_role,
                    'initials': f"{current_user.first_name[:1]}{current_user.last_name[:1]}",
                },
                'scanned_data':   scanned_text,
                'barcode_format': barcode_format,
                'timestamp': timezone.now().strftime('%Y-%m-%d %I:%M:%S %p'),
            })

        else:
            _log(current_user, zone, scanned_text, barcode_format, 'UNAUTHORIZED_ROLE', selected_room, ip, device)

            return JsonResponse({
                'status': 'denied',
                'reason': (
                    f'Your role ({user_role}) cannot access {zone.name}. '
                    f'Allowed: {", ".join(allowed)}'
                ),
                'sound':        'denied',
                'scanned_data': scanned_text,
            })

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid data', 'sound': 'error'}, status=400)
    except Exception as e:
        logger.exception(f"Scan error: {e}")
        # Log the error
        try:
            _log(None, None, str(e)[:200], 'error', 'SCAN_ERROR', '', '', '')
        except Exception:
            pass
        return JsonResponse({'status': 'error', 'message': 'Server error', 'sound': 'error'}, status=500)


def _log(user, zone, text, fmt, result, room, ip, device):
    try:
        BarcodeAccessLog.objects.create(
            user=user,
            zone=zone,
            scanned_text=text,
            barcode_format=fmt,
            access_result=result,
            room_selected=room,
            ip_address=ip or None,
            device_info=device[:500],
        )
    except Exception as e:
        logger.error(f"Log write failed: {e}")


def _get_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@login_required
def access_logs_view(request):
    if not request.user.is_superuser and request.user.role != 'ADMIN':
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('Admin only.')

    logs = BarcodeAccessLog.objects.select_related('user', 'zone').order_by('-timestamp')[:200]

    # Stats
    today = timezone.now().date()
    total_today    = BarcodeAccessLog.objects.filter(timestamp__date=today).count()
    granted_today  = BarcodeAccessLog.objects.filter(timestamp__date=today, access_result='GRANTED').count()
    denied_today   = BarcodeAccessLog.objects.filter(timestamp__date=today, access_result__in=['DENIED','UNAUTHORIZED_ROLE','NOT_LOGGED_IN']).count()
    unknown_today  = BarcodeAccessLog.objects.filter(timestamp__date=today, access_result='UNKNOWN_CODE').count()

    return render(request, 'access_control/logs.html', {
        'logs':          logs,
        'total_today':   total_today,
        'granted_today': granted_today,
        'denied_today':  denied_today,
        'unknown_today': unknown_today,
    })