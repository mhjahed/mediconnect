# dashboard/views.py — COMPLETE CLEAN FILE

import json
import logging
from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum

from accounts.models import DoctorAttendance, AdminNotice, CustomUser

logger = logging.getLogger('mediconnect')


# ══════════════════════════════════════════════════════════════
# ROUTER — Direct user to their proper dashboard
# ══════════════════════════════════════════════════════════════
@login_required
def home_view(request):
    user = request.user

    if user.role == 'DOCTOR':
        return doctor_dashboard(request)

    elif user.role == 'PATIENT':
        return patient_dashboard(request)

    elif user.role == 'ADMIN' or user.is_superuser:
        return redirect('dashboard:admin_home')

    elif user.role in ['NURSE', 'STAFF']:
        return staff_dashboard(request)

    return redirect('accounts:home')


# ══════════════════════════════════════════════════════════════
# DOCTOR DASHBOARD
# ══════════════════════════════════════════════════════════════
@login_required
def doctor_dashboard(request):
    user  = request.user
    today = timezone.now().date()

    try:
        from appointments.models import Appointment

        todays_appointments = Appointment.objects.filter(
            doctor=user,
            appointment_date=today,
            payment_status='PAID',
        ).select_related('patient').order_by('start_time')

        upcoming = Appointment.objects.filter(
            doctor=user,
            appointment_date__gt=today,
            appointment_date__lte=today + timedelta(days=7),
            payment_status='PAID',
        ).select_related('patient').order_by('appointment_date', 'start_time')[:5]

        week_start = today - timedelta(days=6)
        weekly_labels   = []
        weekly_data     = []
        weekly_earnings = []

        for i in range(7):
            day   = week_start + timedelta(days=i)
            count = Appointment.objects.filter(
                doctor=user, appointment_date=day, payment_status='PAID'
            ).count()
            earnings = Appointment.objects.filter(
                doctor=user, appointment_date=day, payment_status='PAID'
            ).aggregate(total=Sum('amount'))['total'] or 0

            weekly_labels.append(day.strftime('%a'))
            weekly_data.append(count)
            weekly_earnings.append(float(earnings))

        total_patients  = Appointment.objects.filter(doctor=user, payment_status='PAID').values('patient').distinct().count()
        total_this_week = Appointment.objects.filter(doctor=user, appointment_date__gte=week_start, payment_status='PAID').count()
        total_earnings  = Appointment.objects.filter(doctor=user, payment_status='PAID').aggregate(total=Sum('amount'))['total'] or 0
        pending_count   = Appointment.objects.filter(doctor=user, status='CONFIRMED', meet_link='', payment_status='PAID').count()

    except Exception as e:
        logger.warning(f"Dashboard data error: {e}")
        todays_appointments = []
        upcoming        = []
        weekly_labels   = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
        weekly_data     = [0]*7
        weekly_earnings = [0]*7
        total_patients  = 0
        total_this_week = 0
        total_earnings  = 0
        pending_count   = 0

    notices = AdminNotice.objects.filter(
        is_active=True
    ).exclude(expires_at__lt=timezone.now()).order_by('-created_at')[:5]

    attendance_streak = 0
    check_date = today
    while DoctorAttendance.objects.filter(doctor=user, date=check_date).exists():
        attendance_streak += 1
        check_date -= timedelta(days=1)

    try:
        doctor_profile = user.doctor_profile
    except Exception:
        doctor_profile = None

    return render(request, 'dashboard/doctor_home.html', {
        'user':                user,
        'doctor_profile':      doctor_profile,
        'today':               today,
        'todays_appointments': todays_appointments,
        'upcoming':            upcoming,
        'notices':             notices,
        'total_patients':      total_patients,
        'total_this_week':     total_this_week,
        'total_earnings':      total_earnings,
        'pending_count':       pending_count,
        'attendance_streak':   attendance_streak,
        'weekly_labels':       json.dumps(weekly_labels),
        'weekly_data':         json.dumps(weekly_data),
        'weekly_earnings':     json.dumps(weekly_earnings),
    })


# ══════════════════════════════════════════════════════════════
# PATIENT DASHBOARD
# ══════════════════════════════════════════════════════════════
@login_required
def patient_dashboard(request):
    user  = request.user
    today = timezone.now().date()

    try:
        from appointments.models import Appointment

        upcoming_paid = Appointment.objects.filter(
            patient=user,
            appointment_date__gte=today,
            payment_status='PAID',
        ).select_related('doctor', 'doctor__doctor_profile').order_by('appointment_date', 'start_time')

        unpaid_pending = Appointment.objects.filter(
            patient=user,
            payment_status='UNPAID',
            status='PENDING',
        ).select_related('doctor', 'doctor__doctor_profile').order_by('appointment_date')

        past = Appointment.objects.filter(
            patient=user,
            appointment_date__lt=today,
            payment_status='PAID',
        ).select_related('doctor').order_by('-appointment_date')[:5]

        total_consultations = Appointment.objects.filter(
            patient=user, payment_status='PAID'
        ).count()

        has_unpaid = unpaid_pending.exists()

    except Exception:
        upcoming_paid = []
        unpaid_pending = []
        past = []
        total_consultations = 0
        has_unpaid = False

    return render(request, 'dashboard/patient_home.html', {
        'user':                user,
        'upcoming':            upcoming_paid,
        'unpaid_pending':      unpaid_pending,
        'past':                past,
        'total_consultations': total_consultations,
        'has_unpaid':          has_unpaid,
        'today':               today,
    })


# ══════════════════════════════════════════════════════════════
# STAFF DASHBOARD (Nurses, Ward Boys, IT, HR, etc.)
# ══════════════════════════════════════════════════════════════
@login_required
def staff_dashboard(request):
    """Dashboard for non-doctor staff members"""
    user  = request.user
    today = timezone.now().date()

    try:
        staff_profile = user.staff_profile
    except Exception:
        staff_profile = None

    notices = AdminNotice.objects.filter(
        is_active=True
    ).exclude(expires_at__lt=timezone.now()).order_by('-created_at')[:5]

    # Get ID card info if exists
    try:
        id_card = user.id_card
        allowed_zones = id_card.allowed_zones.all() if id_card else []
    except Exception:
        id_card = None
        allowed_zones = []

    return render(request, 'dashboard/staff_home.html', {
        'user':           user,
        'staff_profile':  staff_profile,
        'today':          today,
        'notices':        notices,
        'id_card':        id_card,
        'allowed_zones':  allowed_zones,
    })


# ══════════════════════════════════════════════════════════════
# LEGACY admin_dashboard — redirects to new admin home
# ══════════════════════════════════════════════════════════════
@login_required
def admin_dashboard(request):
    return redirect('dashboard:admin_home')


# ══════════════════════════════════════════════════════════════
# ATTENDANCE VIEWS
# ══════════════════════════════════════════════════════════════
from django.views.decorators.csrf import ensure_csrf_cookie

@login_required
@ensure_csrf_cookie    # ⬅ ADD THIS DECORATOR - forces CSRF cookie
def attendance_view(request):
    """Attendance page — all staff types"""
    if request.user.role not in ['DOCTOR', 'NURSE', 'STAFF']:
        return redirect('dashboard:home')

    if DoctorAttendance.has_marked_today(request.user):
        return redirect('dashboard:home')

    return render(request, 'dashboard/attendance.html', {
        'user':  request.user,
        'today': timezone.now().date(),
    })


@login_required
@require_http_methods(['POST'])
def mark_attendance_view(request):
    """API endpoint to mark attendance for staff"""

    # Check role permission
    if request.user.role not in ['DOCTOR', 'NURSE', 'STAFF']:
        return JsonResponse({
            'status':  'error',
            'message': 'Only doctors, nurses, and staff can mark attendance.',
        }, status=403)

    # Already marked check
    if DoctorAttendance.has_marked_today(request.user):
        return JsonResponse({
            'status':  'already_marked',
            'message': 'Attendance already recorded for today.',
        })

    # Create attendance record
    attendance = DoctorAttendance.objects.create(
        doctor=request.user,
        date=timezone.now().date(),
    )

    # Personalized greeting based on role
    role_greeting = {
        'DOCTOR': f'Welcome, Dr. {request.user.last_name}!',
        'NURSE':  f'Welcome, Nurse {request.user.first_name}!',
        'STAFF':  f'Welcome, {request.user.first_name}!',
    }

    return JsonResponse({
        'status':      'success',
        'message':     f'{role_greeting.get(request.user.role)} Have a great shift.',
        'time_in':     attendance.time_in.strftime('%I:%M %p'),
        'doctor_name': request.user.get_full_name(),
        'redirect':    '/dashboard/',
    })