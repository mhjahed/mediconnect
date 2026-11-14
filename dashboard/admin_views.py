# dashboard/admin_views.py — COMPLETE FILE

import logging
from datetime import timedelta
from collections import defaultdict

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Count, Sum, Q

from accounts.models import (
    CustomUser, DoctorProfile, PatientProfile,
    DoctorAccessKey, DoctorAttendance, AdminNotice,
    StaffProfile, StaffAccessKey,
)

logger = logging.getLogger('mediconnect')


# ══════════════════════════════════════════════════════════════
# ADMIN-ONLY DECORATOR
# ══════════════════════════════════════════════════════════════
def admin_required(view_func):
    """Decorator: only superuser or ADMIN role can access"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not (request.user.is_superuser or request.user.role == 'ADMIN'):
            messages.error(request, '🚫 Admin access required.')
            return redirect('dashboard:home')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# ══════════════════════════════════════════════════════════════
# ADMIN HOME
# ══════════════════════════════════════════════════════════════
@login_required
@admin_required
def admin_home(request):
    today = timezone.now().date()

    # Users
    total_doctors  = CustomUser.objects.filter(role='DOCTOR').count()
    total_patients = CustomUser.objects.filter(role='PATIENT').count()
    total_staff    = CustomUser.objects.filter(role__in=['NURSE', 'STAFF']).count()

    # Doctor access keys
    try:
        active_keys = DoctorAccessKey.objects.filter(status='ACTIVE').count()
        used_keys   = DoctorAccessKey.objects.filter(status='USED').count()
        all_keys    = DoctorAccessKey.objects.select_related('generated_by', 'used_by').order_by('-created_at')[:10]
    except Exception:
        active_keys = used_keys = 0
        all_keys = []

    # Staff access keys
    try:
        active_staff_keys = StaffAccessKey.objects.filter(status='ACTIVE').count()
        used_staff_keys   = StaffAccessKey.objects.filter(status='USED').count()
    except Exception:
        active_staff_keys = used_staff_keys = 0

    # Payments
    try:
        from payments.models import PaymentRecord
        pending_payments  = PaymentRecord.objects.filter(payment_status='PENDING').count()
        verified_payments = PaymentRecord.objects.filter(payment_status='VERIFIED').count()
        total_revenue     = PaymentRecord.objects.filter(
            payment_status='VERIFIED'
        ).aggregate(total=Sum('amount'))['total'] or 0

        recent_payments = PaymentRecord.objects.filter(
            payment_status='PENDING'
        ).select_related('patient', 'appointment__doctor').order_by('-submitted_at')[:5]
    except Exception:
        pending_payments = verified_payments = 0
        total_revenue = 0
        recent_payments = []

    # Appointments
    try:
        from appointments.models import Appointment
        todays_appts = Appointment.objects.filter(
            appointment_date=today, payment_status='PAID'
        ).count()
        total_appts = Appointment.objects.filter(payment_status='PAID').count()
    except Exception:
        todays_appts = total_appts = 0

    # Attendance
    attending_today = DoctorAttendance.objects.filter(date=today).count()

    # Notices
    notices = AdminNotice.objects.all().order_by('-created_at')[:5]

    return render(request, 'dashboard/admin_home.html', {
        'total_doctors':     total_doctors,
        'total_patients':    total_patients,
        'total_staff':       total_staff,
        'active_keys':       active_keys,
        'used_keys':         used_keys,
        'active_staff_keys': active_staff_keys,
        'used_staff_keys':   used_staff_keys,
        'all_keys':          all_keys,
        'pending_payments':  pending_payments,
        'verified_payments': verified_payments,
        'total_revenue':     total_revenue,
        'recent_payments':   recent_payments,
        'todays_appts':      todays_appts,
        'total_appts':       total_appts,
        'attending_today':   attending_today,
        'notices':           notices,
        'today':             today,
    })


# ══════════════════════════════════════════════════════════════
# DOCTOR KEYS
# ══════════════════════════════════════════════════════════════
@login_required
@admin_required
def manage_keys(request):
    keys         = DoctorAccessKey.objects.select_related('generated_by', 'used_by').order_by('-created_at')
    specialties  = DoctorProfile.SPECIALTIES
    active_count = keys.filter(status='ACTIVE').count()
    used_count   = keys.filter(status='USED').count()

    return render(request, 'dashboard/admin_keys.html', {
        'keys':         keys,
        'specialties':  specialties,
        'active_count': active_count,
        'used_count':   used_count,
    })


@login_required
@admin_required
def generate_key(request):
    if request.method == 'POST':
        specialty = request.POST.get('specialty', '').strip()
        notes     = request.POST.get('notes', '').strip()

        if not specialty:
            messages.error(request, 'Please select a specialty.')
            return redirect('dashboard:admin_keys')

        key = DoctorAccessKey.objects.create(
            key          = DoctorAccessKey.generate_key(),
            specialty    = specialty,
            generated_by = request.user,
            notes        = notes,
            status       = 'ACTIVE',
        )

        messages.success(request, f'✅ Key generated: {key.key} for {key.get_specialty_display()}')
        return redirect('dashboard:admin_keys')

    return redirect('dashboard:admin_keys')


@login_required
@admin_required
def revoke_key(request, key_id):
    key = get_object_or_404(DoctorAccessKey, id=key_id, status='ACTIVE')
    key.status = 'REVOKED'
    key.save()
    messages.success(request, f'Key {key.key} revoked.')
    return redirect('dashboard:admin_keys')


# ══════════════════════════════════════════════════════════════
# STAFF MANAGEMENT — NEW
# ══════════════════════════════════════════════════════════════
@login_required
@admin_required
def manage_staff(request):
    """List all staff members (nurses, ward boys, IT, etc.)"""
    staff_members = CustomUser.objects.filter(
        role__in=['NURSE', 'STAFF']
    ).select_related('staff_profile').order_by('-date_joined')

    today = timezone.now().date()
    for staff in staff_members:
        staff.attended_today = DoctorAttendance.objects.filter(
            doctor=staff, date=today
        ).exists()

    # Group by department
    by_department = defaultdict(list)
    for s in staff_members:
        if hasattr(s, 'staff_profile') and s.staff_profile:
            dept_name = s.staff_profile.get_department_display()
            by_department[dept_name].append(s)

    return render(request, 'dashboard/admin_staff.html', {
        'staff_members': staff_members,
        'by_department': dict(by_department),
        'total_staff':   staff_members.count(),
        'today':         today,
    })


@login_required
@admin_required
def manage_staff_keys(request):
    """Generate/view staff access keys"""
    keys = StaffAccessKey.objects.select_related(
        'generated_by', 'used_by'
    ).order_by('-created_at')

    active_count = keys.filter(status='ACTIVE').count()
    used_count   = keys.filter(status='USED').count()

    return render(request, 'dashboard/admin_staff_keys.html', {
        'keys':         keys,
        'departments':  StaffProfile.STAFF_DEPARTMENTS,
        'designations': StaffProfile.DESIGNATIONS,
        'active_count': active_count,
        'used_count':   used_count,
    })


@login_required
@admin_required
def generate_staff_key(request):
    """Generate new staff access key"""
    if request.method == 'POST':
        role        = request.POST.get('role', 'STAFF')
        department  = request.POST.get('department', '').strip()
        designation = request.POST.get('designation', '').strip()
        notes       = request.POST.get('notes', '').strip()

        if not department or not designation:
            messages.error(request, 'Department and designation are required.')
            return redirect('dashboard:admin_staff_keys')

        key = StaffAccessKey.objects.create(
            key          = StaffAccessKey.generate_key(),
            role         = role,
            department   = department,
            designation  = designation,
            generated_by = request.user,
            notes        = notes,
            status       = 'ACTIVE',
        )

        messages.success(
            request,
            f'✅ Key generated: {key.key} for {key.get_designation_display()}'
        )
        return redirect('dashboard:admin_staff_keys')

    return redirect('dashboard:admin_staff_keys')


@login_required
@admin_required
def revoke_staff_key(request, key_id):
    key = get_object_or_404(StaffAccessKey, id=key_id, status='ACTIVE')
    key.status = 'REVOKED'
    key.save()
    messages.success(request, f'Key {key.key} revoked.')
    return redirect('dashboard:admin_staff_keys')


# ══════════════════════════════════════════════════════════════
# NOTICES
# ══════════════════════════════════════════════════════════════
@login_required
@admin_required
def post_notice(request):
    if request.method == 'POST':
        title    = request.POST.get('title', '').strip()
        content  = request.POST.get('content', '').strip()
        priority = request.POST.get('priority', 'NORMAL')

        if not title or not content:
            messages.error(request, 'Title and content are required.')
            return redirect('dashboard:admin_notices')

        notice = AdminNotice.objects.create(
            title     = title,
            content   = content,
            priority  = priority,
            posted_by = request.user,
            is_active = True,
        )

        # Broadcast to doctors via notification service
        try:
            from notifications.services import NotificationService
            NotificationService.broadcast_admin_notice(notice)
        except Exception as e:
            logger.warning(f"Broadcast failed: {e}")

        messages.success(request, f'✅ Notice "{title}" posted to all doctor dashboards.')
        return redirect('dashboard:admin_notices')

    return redirect('dashboard:admin_notices')


@login_required
@admin_required
def manage_notices(request):
    notices = AdminNotice.objects.select_related('posted_by').order_by('-created_at')
    return render(request, 'dashboard/admin_notices.html', {
        'notices': notices,
    })


@login_required
@admin_required
def deactivate_notice(request, notice_id):
    notice = get_object_or_404(AdminNotice, id=notice_id)
    notice.is_active = False
    notice.save()
    messages.success(request, f'Notice "{notice.title}" deactivated.')
    return redirect('dashboard:admin_notices')


# ══════════════════════════════════════════════════════════════
# DOCTORS LIST
# ══════════════════════════════════════════════════════════════
# dashboard/admin_views.py — UPDATE the manage_doctors function

@login_required
@admin_required
def manage_doctors(request):
    """Admin view of all doctors — uses SAME card design as patient search"""

    query     = request.GET.get('q', '').strip()
    specialty = request.GET.get('specialty', '').strip()

    doctors = CustomUser.objects.filter(
        role='DOCTOR'
    ).select_related('doctor_profile').order_by('-date_joined')

    # Apply search filter
    if query:
        doctors = doctors.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(doctor_profile__specialty__icontains=query)
        )

    if specialty:
        doctors = doctors.filter(doctor_profile__specialty=specialty)

    today = timezone.now().date()
    for doc in doctors:
        doc.attended_today = DoctorAttendance.objects.filter(
            doctor=doc, date=today
        ).exists()
        try:
            from appointments.models import Appointment
            doc.total_appointments = Appointment.objects.filter(
                doctor=doc, payment_status='PAID'
            ).count()
            doc.patient_count = Appointment.objects.filter(
                doctor=doc, payment_status='PAID'
            ).values('patient').distinct().count()
        except Exception:
            doc.total_appointments = 0
            doc.patient_count = 0

    specialties = DoctorProfile.SPECIALTIES

    return render(request, 'dashboard/admin_doctors.html', {
        'doctors':      doctors,
        'specialties':  specialties,
        'query':        query,
        'specialty':    specialty,
        'today':        today,
        'result_count': doctors.count(),
    })
# ══════════════════════════════════════════════════════════════
# PATIENTS LIST
# ══════════════════════════════════════════════════════════════
@login_required
@admin_required
def manage_patients(request):
    patients = CustomUser.objects.filter(
        role='PATIENT'
    ).select_related('patient_profile').order_by('-date_joined')

    return render(request, 'dashboard/admin_patients.html', {
        'patients': patients,
    })


# ══════════════════════════════════════════════════════════════
# PAYMENT VERIFICATION
# ══════════════════════════════════════════════════════════════
@login_required
@admin_required
def payment_verification(request):
    from payments.models import PaymentRecord

    pending  = PaymentRecord.objects.filter(
        payment_status='PENDING'
    ).select_related('patient', 'appointment', 'appointment__doctor').order_by('-submitted_at')

    verified = PaymentRecord.objects.filter(
        payment_status='VERIFIED'
    ).select_related('patient', 'appointment').order_by('-verified_at')[:20]

    rejected = PaymentRecord.objects.filter(
        payment_status='REJECTED'
    ).select_related('patient').order_by('-updated_at')[:10]

    return render(request, 'dashboard/admin_payments.html', {
        'pending':  pending,
        'verified': verified,
        'rejected': rejected,
    })


@login_required
@admin_required
def verify_payment(request, payment_id):
    from payments.models import PaymentRecord

    payment = get_object_or_404(PaymentRecord, id=payment_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'verify':
            payment.payment_status = 'VERIFIED'
            payment.verified_by    = request.user
            payment.verified_at    = timezone.now()
            payment.save()

            payment.appointment.payment_status = 'PAID'
            payment.appointment.status         = 'CONFIRMED'
            payment.appointment.save(update_fields=['payment_status', 'status'])

            # Send notification
            try:
                from notifications.services import NotificationService
                NotificationService.send_appointment_confirmed(payment.appointment)
            except Exception as e:
                logger.warning(f"Notification failed: {e}")

            messages.success(request, f'✅ Payment verified for {payment.patient.get_full_name()}')

        elif action == 'reject':
            reason = request.POST.get('rejection_reason', 'Could not verify payment details.')
            payment.payment_status   = 'REJECTED'
            payment.rejection_reason = reason
            payment.save()

            try:
                from notifications.services import NotificationService
                NotificationService.send_payment_rejected(payment, reason)
            except Exception as e:
                logger.warning(f"Notification failed: {e}")

            messages.warning(request, f'❌ Payment rejected for {payment.patient.get_full_name()}')

    return redirect('dashboard:admin_payments')


# ══════════════════════════════════════════════════════════════
# ID CARD MANAGEMENT
# ══════════════════════════════════════════════════════════════
@login_required
@admin_required
def manage_staff_ids(request):
    """List all staff ID cards"""
    from access_control.models import StaffIDCard

    cards = StaffIDCard.objects.select_related('user').prefetch_related('allowed_zones').order_by('-created_at')

    # Staff without cards — INCLUDES doctors, nurses, and staff
    staff_without_cards = CustomUser.objects.filter(
        role__in=['DOCTOR', 'NURSE', 'STAFF', 'ADMIN'],
        id_card__isnull=True
    )

    return render(request, 'dashboard/admin_id_cards.html', {
        'cards':               cards,
        'staff_without_cards': staff_without_cards,
        'total_cards':         cards.count(),
        'active_cards':        cards.filter(status='ACTIVE').count(),
    })


@login_required
@admin_required
def generate_id_card(request, user_id):
    """Generate ID card for any staff member"""
    from access_control.models import StaffIDCard, AccessZone, PersonalAccessBarcode

    staff = get_object_or_404(
        CustomUser, id=user_id,
        role__in=['DOCTOR', 'NURSE', 'STAFF', 'ADMIN']
    )

    if hasattr(staff, 'id_card'):
        messages.warning(request, f'{staff.get_full_name()} already has an ID card.')
        return redirect('dashboard:edit_id_card', card_id=staff.id_card.id)

    all_zones = AccessZone.objects.filter(is_active=True).order_by('floor_number', 'name')

    floors = {}
    for zone in all_zones:
        floor = zone.floor_number
        if floor not in floors:
            floors[floor] = []
        floors[floor].append(zone)

    if request.method == 'POST':
        designation       = request.POST.get('designation', '').strip()
        department        = request.POST.get('department', '').strip()
        desk_number       = request.POST.get('desk_number', '').strip()
        blood_group       = request.POST.get('blood_group', '').strip()
        valid_months      = int(request.POST.get('valid_months', 24))
        selected_zone_ids = request.POST.getlist('zones')

        if not designation:
            messages.error(request, 'Designation is required.')
            return render(request, 'dashboard/admin_generate_id.html', {
                'staff': staff, 'floors': dict(sorted(floors.items())),
            })

        card = StaffIDCard.objects.create(
            user            = staff,
            staff_id_number = StaffIDCard.generate_staff_id(),
            access_code     = StaffIDCard.generate_access_code(staff),
            designation     = designation,
            department      = department,
            desk_number     = desk_number,
            blood_group     = blood_group,
            valid_till      = timezone.now().date() + timedelta(days=valid_months * 30),
            issued_by       = request.user,
        )

        if selected_zone_ids:
            zones = AccessZone.objects.filter(id__in=selected_zone_ids)
            card.allowed_zones.set(zones)

        PersonalAccessBarcode.objects.create(
            user         = staff,
            barcode_text = card.access_code,
            is_active    = True,
        )

        messages.success(
            request,
            f'✅ ID Card #{card.staff_id_number} generated for {staff.get_full_name()}!'
        )
        return redirect('dashboard:view_id_card', card_id=card.id)

    return render(request, 'dashboard/admin_generate_id.html', {
        'staff':       staff,
        'floors':      dict(sorted(floors.items())),
        'total_zones': all_zones.count(),
    })


@login_required
@admin_required
def view_id_card(request, card_id):
    from access_control.models import StaffIDCard
    card = get_object_or_404(StaffIDCard, id=card_id)
    return render(request, 'dashboard/admin_view_id_cards.html', {
        'card': card,
    })


@login_required
@admin_required
def edit_id_card(request, card_id):
    from access_control.models import StaffIDCard, AccessZone

    card      = get_object_or_404(StaffIDCard, id=card_id)
    all_zones = AccessZone.objects.filter(is_active=True).order_by('floor_number', 'name')

    floors = {}
    for zone in all_zones:
        floor = zone.floor_number
        if floor not in floors:
            floors[floor] = []
        floors[floor].append(zone)

    current_zone_ids = set(card.allowed_zones.values_list('id', flat=True))

    if request.method == 'POST':
        selected_zone_ids = request.POST.getlist('zones')
        zones = AccessZone.objects.filter(id__in=selected_zone_ids)
        card.allowed_zones.set(zones)

        card.designation = request.POST.get('designation', card.designation).strip()
        card.desk_number = request.POST.get('desk_number', card.desk_number).strip()
        card.save()

        messages.success(request, f'✅ ID Card updated for {card.user.get_full_name()}')
        return redirect('dashboard:view_id_card', card_id=card.id)

    return render(request, 'dashboard/admin_generate_id.html', {
        'staff':            card.user,
        'card':             card,
        'floors':           dict(sorted(floors.items())),
        'current_zone_ids': current_zone_ids,
        'editing':          True,
    })


@login_required
@admin_required
def print_barcode_sheet(request):
    """Print a sheet of all staff barcodes for ID cards"""
    from access_control.models import StaffIDCard

    cards = StaffIDCard.objects.filter(
        status='ACTIVE'
    ).select_related('user').order_by('user__role', 'user__first_name')

    return render(request, 'dashboard/admin_barcode_sheet.html', {
        'cards': cards,
    })