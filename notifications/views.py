# notifications/views.py

import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Notification

logger = logging.getLogger('mediconnect')


# ══════════════════════════════════════════════════════════════
# NOTIFICATION CENTER (Full page)
# ══════════════════════════════════════════════════════════════
@login_required
def notification_center(request):
    """Full notification history page"""
    user = request.user

    # Filter
    filter_type = request.GET.get('filter', 'all')

    notifications = Notification.objects.filter(recipient=user)

    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)
    elif filter_type == 'read':
        notifications = notifications.filter(is_read=True)

    notifications = notifications.order_by('-created_at')[:100]

    unread_count = Notification.objects.filter(recipient=user, is_read=False).count()
    total_count  = Notification.objects.filter(recipient=user).count()

    return render(request, 'notifications/center.html', {
        'notifications': notifications,
        'unread_count':  unread_count,
        'total_count':   total_count,
        'filter':        filter_type,
    })


# ══════════════════════════════════════════════════════════════
# API — Get unread count + recent notifications (bell dropdown)
# ══════════════════════════════════════════════════════════════
@login_required
def api_notifications(request):
    """Returns recent notifications for bell dropdown"""
    user = request.user

    recent = Notification.objects.filter(
        recipient=user
    ).order_by('-created_at')[:10]

    unread_count = Notification.objects.filter(
        recipient=user, is_read=False
    ).count()

    notifications_data = []
    for n in recent:
        notifications_data.append({
            'id':            str(n.id),
            'icon':          n.icon,
            'title':         n.title,
            'message':       n.message[:120],
            'is_read':       n.is_read,
            'priority':      n.priority,
            'action_url':    n.action_url,
            'action_label':  n.action_label,
            'created_at':    n.created_at.strftime('%b %d, %I:%M %p'),
            'time_ago':      _time_ago(n.created_at),
        })

    return JsonResponse({
        'unread_count':  unread_count,
        'notifications': notifications_data,
    })


# ══════════════════════════════════════════════════════════════
# API — Mark single notification as read
# ══════════════════════════════════════════════════════════════
@login_required
@require_http_methods(['POST'])
def api_mark_read(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notif.mark_as_read()
    return JsonResponse({'success': True})


# ══════════════════════════════════════════════════════════════
# API — Mark ALL as read
# ══════════════════════════════════════════════════════════════
@login_required
@require_http_methods(['POST'])
def api_mark_all_read(request):
    Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).update(is_read=True, read_at=timezone.now())

    return JsonResponse({'success': True, 'message': 'All notifications marked as read'})


# ══════════════════════════════════════════════════════════════
# Delete notification
# ══════════════════════════════════════════════════════════════
@login_required
@require_http_methods(['POST'])
def api_delete_notification(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notif.delete()
    return JsonResponse({'success': True})


# ══════════════════════════════════════════════════════════════
# Click notification → mark read + redirect
# ══════════════════════════════════════════════════════════════
@login_required
def open_notification(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notif.mark_as_read()

    if notif.action_url:
        return redirect(notif.action_url)
    return redirect('notifications:center')


# ══════════════════════════════════════════════════════════════
# HELPER
# ══════════════════════════════════════════════════════════════
def _time_ago(dt):
    """Human-friendly time difference"""
    delta = timezone.now() - dt
    seconds = delta.total_seconds()

    if seconds < 60:
        return 'Just now'
    elif seconds < 3600:
        m = int(seconds // 60)
        return f'{m} min{"s" if m != 1 else ""} ago'
    elif seconds < 86400:
        h = int(seconds // 3600)
        return f'{h} hour{"s" if h != 1 else ""} ago'
    elif seconds < 604800:
        d = int(seconds // 86400)
        return f'{d} day{"s" if d != 1 else ""} ago'
    else:
        return dt.strftime('%b %d')