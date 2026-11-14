# medical_records/views.py — COMPLETE FIXED FILE

import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone

from appointments.models import Appointment
from .models import MedicalRecord, Prescription, LabTest
from .forms import MedicalRecordForm, PrescriptionFormSet, LabTestFormSet

logger = logging.getLogger('mediconnect')


# ══════════════════════════════════════════════════════════════
# PATIENT — Medical history
# ══════════════════════════════════════════════════════════════
@login_required
def records_home(request):
    user = request.user

    if user.role == 'PATIENT':
        records = MedicalRecord.objects.filter(
            patient=user,
            appointment__payment_status='PAID',
        ).select_related(
            'doctor', 'doctor__doctor_profile', 'appointment'
        ).order_by('-created_at')

        locked_appointments = Appointment.objects.filter(
            patient=user,
            payment_status='UNPAID',
            status='PENDING',
        ).select_related('doctor')

        return render(request, 'medical_records/history.html', {
            'records':             records,
            'locked_appointments': locked_appointments,
        })

    elif user.role == 'DOCTOR':
        return doctor_records(request)

    return redirect('dashboard:home')


# ══════════════════════════════════════════════════════════════
# DOCTOR — Records list
# ══════════════════════════════════════════════════════════════
@login_required
def doctor_records(request):
    """Doctor sees all records they have written"""
    if request.user.role != 'DOCTOR':
        return redirect('dashboard:home')

    records = MedicalRecord.objects.filter(
        doctor=request.user
    ).select_related(
        'patient', 'appointment'
    ).order_by('-created_at')

    return render(request, 'medical_records/doctor_records.html', {
        'records': records,
    })


# ══════════════════════════════════════════════════════════════
# VIEW SINGLE RECORD
# ══════════════════════════════════════════════════════════════
@login_required
def record_detail(request, record_id):
    record = get_object_or_404(MedicalRecord, id=record_id)

    if not record.has_access(request.user):
        return HttpResponseForbidden(
            '🔒 Access Denied. This record is locked until payment is verified.'
        )

    prescriptions = record.prescriptions.all().order_by('order_number')
    lab_tests     = record.lab_tests.all()

    return render(request, 'medical_records/record_detail.html', {
        'record':        record,
        'prescriptions': prescriptions,
        'lab_tests':     lab_tests,
    })


# ══════════════════════════════════════════════════════════════
# CREATE / EDIT RECORD (Doctor only)
# ══════════════════════════════════════════════════════════════
@login_required
def create_or_edit_record(request, appointment_id):
    """Doctor creates/edits a consultation record"""
    if request.user.role != 'DOCTOR':
        return HttpResponseForbidden('Doctors only.')

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=request.user,
        payment_status='PAID',
    )

    record, created = MedicalRecord.objects.get_or_create(
        appointment=appointment,
        defaults={
            'patient':         appointment.patient,
            'doctor':          request.user,
            'chief_complaint': appointment.chief_complaint,
        }
    )

    if request.method == 'POST':
        form        = MedicalRecordForm(request.POST, instance=record)
        rx_formset  = PrescriptionFormSet(request.POST, instance=record, prefix='rx')
        lab_formset = LabTestFormSet(request.POST, instance=record, prefix='lab')

        if form.is_valid() and rx_formset.is_valid() and lab_formset.is_valid():
            record = form.save()
            rx_formset.save()
            lab_formset.save()

            # Set order numbers
            for i, rx in enumerate(record.prescriptions.all(), 1):
                rx.order_number = i
                rx.save(update_fields=['order_number'])

            # ── If finalized: complete appointment + notify patient ──
            if record.is_finalized:
                appointment.status = 'COMPLETED'
                appointment.save(update_fields=['status'])

                # 🔔 Send in-app notification to patient
                try:
                    from notifications.services import NotificationService
                    NotificationService.send_record_available(record)
                except Exception as e:
                    logger.error(f"Notification failed: {e}")

            messages.success(request, '✅ Consultation record saved successfully.')
            logger.info(f"Record saved: {record.id} by Dr.{request.user.get_full_name()}")
            return redirect('medical_records:record_detail', record_id=record.id)

        else:
            messages.error(request, '❌ Please fix the errors below.')

    else:
        form        = MedicalRecordForm(instance=record)
        rx_formset  = PrescriptionFormSet(instance=record, prefix='rx')
        lab_formset = LabTestFormSet(instance=record, prefix='lab')

    return render(request, 'medical_records/create_record.html', {
        'form':        form,
        'rx_formset':  rx_formset,
        'lab_formset': lab_formset,
        'record':      record,
        'appointment': appointment,
        'patient':     appointment.patient,
        'created':     created,
    })


# ══════════════════════════════════════════════════════════════
# PRINT PRESCRIPTION
# ══════════════════════════════════════════════════════════════
@login_required
def print_prescription(request, record_id):
    record = get_object_or_404(MedicalRecord, id=record_id)

    if not record.has_access(request.user):
        return HttpResponseForbidden('🔒 Access denied.')

    prescriptions = record.prescriptions.all().order_by('order_number')
    lab_tests     = record.lab_tests.all()

    # ── Calculate patient age safely ──
    patient_age = None
    if record.patient.date_of_birth:
        today = timezone.now().date()
        dob   = record.patient.date_of_birth
        patient_age = today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day)
        )

    # ── Get gender display ──
    gender_map = {'MALE': 'Male', 'FEMALE': 'Female', 'OTHER': 'Other'}
    patient_gender = gender_map.get(record.patient.gender, 'N/A')

    return render(request, 'medical_records/prescription_print.html', {
        'record':        record,
        'prescriptions': prescriptions,
        'lab_tests':     lab_tests,
        'patient_age':   patient_age,
        'patient_gender': patient_gender,
        'print_mode':    True,
    })