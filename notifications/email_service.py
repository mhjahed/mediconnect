# notifications/email_service.py

import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('mediconnect')


def send_meet_confirmation_email(appointment):
    """
    Sends beautiful HTML confirmation emails to BOTH Doctor and Patient.
    Called immediately after Doctor sets the Google Meet link.
    """
    context = _build_email_context(appointment)

    # ── Email to PATIENT ──────────────────────────────
    _dispatch_email(
        subject=f"✅ Your Appointment is Confirmed – {appointment.appointment_date.strftime('%B %d, %Y')}",
        template_name='notifications/email_confirmation_patient.html',
        context={**context, 'recipient_type': 'patient'},
        to_email=appointment.patient.email,
        to_name=appointment.patient.get_full_name(),
    )

    # ── Email to DOCTOR ───────────────────────────────
    _dispatch_email(
        subject=f"📅 Meeting Scheduled – {appointment.patient.get_full_name()} | {appointment.appointment_date.strftime('%B %d, %Y')}",
        template_name='notifications/email_confirmation_doctor.html',
        context={**context, 'recipient_type': 'doctor'},
        to_email=appointment.doctor.email,
        to_name=f"Dr. {appointment.doctor.get_full_name()}",
    )

    logger.info(f"Confirmation emails sent | Appt: {appointment.id}")


def send_reminder_email(appointment):
    """
    Sends 10-minute reminder to BOTH Doctor and Patient.
    Called by the background management command.
    """
    context = _build_email_context(appointment)

    # Patient reminder
    _dispatch_email(
        subject="⏰ Reminder: Your consultation starts in 10 minutes!",
        template_name='notifications/email_reminder_patient.html',
        context={**context, 'recipient_type': 'patient'},
        to_email=appointment.patient.email,
        to_name=appointment.patient.get_full_name(),
    )

    # Doctor reminder
    _dispatch_email(
        subject=f"⏰ Reminder: Consultation with {appointment.patient.get_full_name()} in 10 minutes",
        template_name='notifications/email_reminder_doctor.html',
        context={**context, 'recipient_type': 'doctor'},
        to_email=appointment.doctor.email,
        to_name=f"Dr. {appointment.doctor.get_full_name()}",
    )

    logger.info(f"10-min reminder emails sent | Appt: {appointment.id}")


def _build_email_context(appointment):
    """Builds shared context dict for all email templates"""
    try:
        doctor_profile = appointment.doctor.doctor_profile
        specialty = doctor_profile.get_specialty_display()
        consultation_fee = doctor_profile.consultation_fee
    except Exception:
        specialty = 'General Practice'
        consultation_fee = appointment.amount

    meeting_dt = appointment.meeting_time or appointment.get_meeting_datetime()

    return {
        'appointment':      appointment,
        'doctor':           appointment.doctor,
        'patient':          appointment.patient,
        'doctor_name':      f"Dr. {appointment.doctor.get_full_name()}",
        'patient_name':     appointment.patient.get_full_name(),
        'specialty':        specialty,
        'appointment_date': appointment.appointment_date.strftime('%A, %B %d, %Y'),
        'start_time':       appointment.start_time.strftime('%I:%M %p'),
        'end_time':         appointment.end_time.strftime('%I:%M %p'),
        'meeting_datetime': meeting_dt.strftime('%A, %B %d, %Y at %I:%M %p'),
        'meet_link':        appointment.meet_link,
        'meet_notes':       appointment.meet_notes,
        'consultation_fee': consultation_fee,
        'appointment_id':   str(appointment.id)[:8].upper(),
        'site_url':         settings.SITE_URL,
        'current_year':     timezone.now().year,
    }


def _dispatch_email(subject, template_name, context, to_email, to_name):
    """Core email dispatcher — sends HTML + plain text fallback"""
    try:
        html_content  = render_to_string(template_name, context)
        plain_content = _strip_to_plain(context)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[f"{to_name} <{to_email}>"],
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send(fail_silently=False)

        logger.info(f"Email sent → {to_email} | Subject: {subject}")

    except Exception as e:
        logger.error(f"Email failed → {to_email} | Error: {e}")
        raise


def _strip_to_plain(context):
    """Plain text fallback for email clients that don't render HTML"""
    return (
        f"MediConnect – Appointment Confirmation\n"
        f"{'='*50}\n"
        f"Doctor: {context.get('doctor_name')}\n"
        f"Patient: {context.get('patient_name')}\n"
        f"Date & Time: {context.get('meeting_datetime')}\n"
        f"Google Meet Link: {context.get('meet_link')}\n"
        f"{'='*50}\n"
        f"Notes: {context.get('meet_notes', 'None')}\n"
        f"\nPowered by MediConnect | {context.get('site_url')}"
    )