# appointments/views.py  — COMPLETE REWRITE with payment rules

import json
import logging
from datetime import datetime, timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from accounts.models import CustomUser, DoctorProfile
from .models import Appointment, DoctorReview
from .forms import AppointmentBookingForm, GoogleMeetSetupForm

logger = logging.getLogger('mediconnect')


# ══════════════════════════════════════════════════════════════
# HOME — List appointments
# ══════════════════════════════════════════════════════════════
@login_required
def appointments_home(request):
    user  = request.user
    today = timezone.now().date()

    if user.role == 'DOCTOR':
        # Doctor ONLY sees appointments with PAID status
        appts = Appointment.objects.filter(
            doctor=user,
            payment_status='PAID',
        ).select_related('patient').order_by('-appointment_date', '-start_time')
    else:
        appts = Appointment.objects.filter(
            patient=user
        ).select_related('doctor', 'doctor__doctor_profile').order_by('-appointment_date', '-start_time')

    upcoming = [a for a in appts if a.appointment_date >= today]
    past     = [a for a in appts if a.appointment_date < today]

    return render(request, 'appointments/list.html', {
        'upcoming': upcoming,
        'past':     past,
        'user':     user,
    })


# ══════════════════════════════════════════════════════════════
# SEARCH DOCTORS
# ══════════════════════════════════════════════════════════════
@login_required
def search_doctors(request):
    query     = request.GET.get('q', '').strip()
    specialty = request.GET.get('specialty', '').strip()

    doctors = CustomUser.objects.filter(
        role='DOCTOR',
        is_active=True
    ).select_related('doctor_profile')

    if query:
        doctors = doctors.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(doctor_profile__specialty__icontains=query) |
            Q(doctor_profile__bio__icontains=query)
        )

    if specialty:
        doctors = doctors.filter(doctor_profile__specialty=specialty)

    for doc in doctors:
        try:
            doc.patient_count = Appointment.objects.filter(
                doctor=doc, payment_status='PAID'
            ).values('patient').distinct().count()
        except Exception:
            doc.patient_count = 0

    specialties = DoctorProfile.SPECIALTIES

    return render(request, 'appointments/search_doctor.html', {
        'doctors':     doctors,
        'query':       query,
        'specialty':   specialty,
        'specialties': specialties,
        'result_count': doctors.count(),
    })


# ══════════════════════════════════════════════════════════════
# DOCTOR PROFILE + BOOKING
# ══════════════════════════════════════════════════════════════
@login_required
def doctor_profile(request, doctor_id):
    doctor = get_object_or_404(CustomUser, id=doctor_id, role='DOCTOR', is_active=True)

    try:
        profile = doctor.doctor_profile
    except Exception:
        profile = None

    reviews = DoctorReview.objects.filter(
        doctor=doctor
    ).select_related('patient').order_by('-created_at')[:10]

    # ── 3-day rule: Slots start from (today + 3 days) ────
    # Patient must pay at least 3 days before appointment
    available_slots = _get_available_slots(doctor, start_offset=3, days_ahead=14)

    # Check if patient has unpaid appointments
    has_unpaid = False
    if request.user.role == 'PATIENT':
        has_unpaid = Appointment.objects.filter(
            patient=request.user,
            payment_status='UNPAID',
            status__in=['PENDING'],
        ).exists()

    return render(request, 'appointments/doctor_profile.html', {
        'doctor':          doctor,
        'profile':         profile,
        'reviews':         reviews,
        'available_slots': json.dumps(available_slots),
        'has_unpaid':      has_unpaid,
    })


# ══════════════════════════════════════════════════════════════
# SLOT GENERATOR — 3-day minimum gap
# ══════════════════════════════════════════════════════════════
def _get_available_slots(doctor, start_offset=3, days_ahead=14):
    """
    start_offset=3 → slots only from today+3 onwards.
    Patient can't book within next 3 days.
    """
    from dashboard.models import DoctorSchedule

    today  = timezone.now().date()
    result = {}
    day_map = {0:'MON', 1:'TUE', 2:'WED', 3:'THU', 4:'FRI', 5:'SAT', 6:'SUN'}

    for i in range(start_offset, start_offset + days_ahead):
        check_date = today + timedelta(days=i)
        day_code   = day_map[check_date.weekday()]

        try:
            schedules = DoctorSchedule.objects.filter(
                doctor=doctor,
                day_of_week=day_code,
                is_available=True,
            )
        except Exception:
            schedules = []

        if not schedules:
            continue

        date_str = check_date.strftime('%Y-%m-%d')
        slots    = []

        for schedule in schedules:
            current = datetime.combine(check_date, schedule.start_time)
            end_dt  = datetime.combine(check_date, schedule.end_time)
            duration = timedelta(minutes=schedule.slot_duration)

            while current + duration <= end_dt:
                slot_start = current.time()
                slot_end   = (current + duration).time()

                is_booked = Appointment.objects.filter(
                    doctor=doctor,
                    appointment_date=check_date,
                    start_time=slot_start,
                    status__in=['PENDING', 'CONFIRMED', 'MEET_SET'],
                ).exists()

                if not is_booked:
                    slots.append({
                        'start': slot_start.strftime('%H:%M'),
                        'end':   slot_end.strftime('%H:%M'),
                        'label': current.strftime('%I:%M %p'),
                    })

                current += duration

        if slots:
            result[date_str] = slots

    return result


# ══════════════════════════════════════════════════════════════
# BOOK APPOINTMENT — Enforces 3-day rule
# ══════════════════════════════════════════════════════════════
@login_required
@require_http_methods(['POST'])
def book_appointment(request, doctor_id):
    if request.user.role != 'PATIENT':
        messages.error(request, 'Only patients can book appointments.')
        return redirect('appointments:search')

    doctor = get_object_or_404(CustomUser, id=doctor_id, role='DOCTOR')

    try:
        profile = doctor.doctor_profile
    except Exception:
        messages.error(request, 'Doctor profile not found.')
        return redirect('appointments:search')

    date_str   = request.POST.get('appointment_date')
    start_time = request.POST.get('start_time')
    end_time   = request.POST.get('end_time')
    complaint  = request.POST.get('chief_complaint', '')

    if not all([date_str, start_time, end_time]):
        messages.error(request, 'Please select a date and time slot.')
        return redirect('appointments:doctor_profile', doctor_id=doctor_id)

    try:
        appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_t   = datetime.strptime(start_time, '%H:%M').time()
        end_t     = datetime.strptime(end_time, '%H:%M').time()
    except ValueError:
        messages.error(request, 'Invalid date or time format.')
        return redirect('appointments:doctor_profile', doctor_id=doctor_id)

    # ── ENFORCE 3-DAY RULE ───────────────────────────────
    today     = timezone.now().date()
    min_date  = today + timedelta(days=3)
    if appt_date < min_date:
        messages.error(
            request,
            f'Appointments must be booked at least 3 days in advance. '
            f'Earliest available date: {min_date.strftime("%B %d, %Y")}'
        )
        return redirect('appointments:doctor_profile', doctor_id=doctor_id)

    # Check slot availability
    already_booked = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=appt_date,
        start_time=start_t,
        status__in=['PENDING', 'CONFIRMED', 'MEET_SET'],
    ).exists()

    if already_booked:
        messages.error(request, 'This slot was just booked. Choose another time.')
        return redirect('appointments:doctor_profile', doctor_id=doctor_id)

    appointment = Appointment.objects.create(
        patient          = request.user,
        doctor           = doctor,
        appointment_date = appt_date,
        start_time       = start_t,
        end_time         = end_t,
        chief_complaint  = complaint,
        amount           = profile.consultation_fee,
        status           = 'PENDING',
        payment_status   = 'UNPAID',
    )

    return redirect('payments:checkout', appointment_id=appointment.id)


# ══════════════════════════════════════════════════════════════
# SETUP GOOGLE MEET — Only for PAID appointments
# ══════════════════════════════════════════════════════════════
@login_required
@require_http_methods(['GET', 'POST'])
def setup_google_meet(request, appointment_id):
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=request.user,
        payment_status='PAID',
    )

    if request.method == 'POST':
        form = GoogleMeetSetupForm(request.POST, instance=appointment)

        if form.is_valid():
            appt = form.save(commit=False)
            appt.status = 'MEET_SET'
            appt.meeting_time = timezone.datetime.combine(
                appt.appointment_date,
                appt.start_time,
                tzinfo=timezone.get_current_timezone()
            )
            if form.cleaned_data.get('custom_meeting_time'):
                appt.meeting_time = form.cleaned_data['custom_meeting_time']

            appt.save()

            try:
                from notifications.email_service import send_meet_confirmation_email
                send_meet_confirmation_email(appt)
                appt.confirmation_sent = True
                appt.save(update_fields=['confirmation_sent'])
                messages.success(request, '✅ Meeting link set! Confirmation emails sent.')
            except Exception as e:
                logger.error(f"Email failed: {e}")
                messages.warning(request, '⚠️ Meeting saved but email failed.')

            return redirect('dashboard:home')
    else:
        form = GoogleMeetSetupForm(instance=appointment)

    return render(request, 'appointments/setup_meet.html', {
        'appointment': appointment,
        'form':        form,
    })


# ══════════════════════════════════════════════════════════════
# API — GET SLOTS (AJAX) — Also enforces 3-day rule
# ══════════════════════════════════════════════════════════════
@login_required
def get_slots_for_date(request, doctor_id):
    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'slots': []})

    doctor = get_object_or_404(CustomUser, id=doctor_id, role='DOCTOR')

    try:
        check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'slots': []})

    # ── 3-day rule check ─────────────────────────────────
    today    = timezone.now().date()
    min_date = today + timedelta(days=3)
    if check_date < min_date:
        return JsonResponse({
            'slots': [],
            'message': 'Appointments must be booked at least 3 days in advance.'
        })

    from dashboard.models import DoctorSchedule
    day_map  = {0:'MON', 1:'TUE', 2:'WED', 3:'THU', 4:'FRI', 5:'SAT', 6:'SUN'}
    day_code = day_map[check_date.weekday()]

    try:
        schedules = DoctorSchedule.objects.filter(
            doctor=doctor, day_of_week=day_code, is_available=True
        )
    except Exception:
        return JsonResponse({'slots': []})

    slots = []
    for schedule in schedules:
        current  = datetime.combine(check_date, schedule.start_time)
        end_dt   = datetime.combine(check_date, schedule.end_time)
        duration = timedelta(minutes=schedule.slot_duration)

        while current + duration <= end_dt:
            slot_start = current.time()
            slot_end   = (current + duration).time()

            is_booked = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=check_date,
                start_time=slot_start,
                status__in=['PENDING', 'CONFIRMED', 'MEET_SET'],
            ).exists()

            if not is_booked:
                slots.append({
                    'start': slot_start.strftime('%H:%M'),
                    'end':   slot_end.strftime('%H:%M'),
                    'label': current.strftime('%I:%M %p'),
                })

            current += duration

    return JsonResponse({'slots': slots, 'date': date_str})


    # appointments/views.py — Update setup_google_meet
# appointments/views.py — Update setup_google_meet

@login_required
@require_http_methods(['GET', 'POST'])
def setup_google_meet(request, appointment_id):
    from notifications.services import NotificationService

    appointment = get_object_or_404(
        Appointment, id=appointment_id,
        doctor=request.user, payment_status='PAID',
    )

    if request.method == 'POST':
        form = GoogleMeetSetupForm(request.POST, instance=appointment)
        if form.is_valid():
            appt = form.save(commit=False)
            appt.status = 'MEET_SET'
            appt.meeting_time = timezone.datetime.combine(
                appt.appointment_date, appt.start_time,
                tzinfo=timezone.get_current_timezone()
            )
            appt.save()

            try:
                from notifications.email_service import send_meet_confirmation_email
                send_meet_confirmation_email(appt)
                appt.confirmation_sent = True
                appt.save(update_fields=['confirmation_sent'])
            except Exception as e:
                logger.error(f"Email failed: {e}")

            # 🔔 Send in-app notification
            NotificationService.send_meet_link_set(appt)

            messages.success(request, '✅ Meeting link saved! Notifications sent.')
            return redirect('dashboard:home')
    else:
        form = GoogleMeetSetupForm(instance=appointment)

    return render(request, 'appointments/setup_meet.html', {
        'appointment': appointment, 'form': form,
    })