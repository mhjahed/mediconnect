# notifications/services.py

import logging
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import Notification, EmailLog

logger = logging.getLogger('mediconnect')


# ══════════════════════════════════════════════════════════════
# CORE NOTIFICATION FACTORY
# ══════════════════════════════════════════════════════════════
class NotificationService:
    """Centralized notification dispatcher"""

    @staticmethod
    def send_appointment_confirmed(appointment):
        """Patient notification when admin verifies payment"""
        Notification.create_notification(
            recipient    = appointment.patient,
            notif_type   = 'APPOINTMENT_CONFIRMED',
            title        = '✅ Appointment Confirmed!',
            message      = (
                f'Your appointment with Dr. {appointment.doctor.get_full_name()} '
                f'on {appointment.appointment_date.strftime("%B %d, %Y")} '
                f'at {appointment.start_time.strftime("%I:%M %p")} is confirmed. '
                f'Awaiting doctor to set the meeting link.'
            ),
            action_url   = f'/appointments/',
            action_label = 'View Appointment',
            priority     = 'HIGH',
            related_obj  = appointment,
        )

        # Notify doctor too
        Notification.create_notification(
            recipient    = appointment.doctor,
            notif_type   = 'NEW_APPOINTMENT',
            title        = '📅 New Confirmed Appointment',
            message      = (
                f'{appointment.patient.get_full_name()} has confirmed their booking '
                f'for {appointment.appointment_date.strftime("%B %d, %Y")} '
                f'at {appointment.start_time.strftime("%I:%M %p")}. '
                f'Please set up the Google Meet link.'
            ),
            action_url   = f'/appointments/setup-meet/{appointment.id}/',
            action_label = 'Set Meet Link',
            priority     = 'HIGH',
            related_obj  = appointment,
        )


    @staticmethod
    def send_payment_rejected(payment, reason):
        Notification.create_notification(
            recipient    = payment.patient,
            notif_type   = 'PAYMENT_REJECTED',
            title        = '❌ Payment Rejected',
            message      = (
                f'Your payment of ৳{payment.amount} could not be verified. '
                f'Reason: {reason}. Please re-submit your payment.'
            ),
            action_url   = f'/payments/checkout/{payment.appointment.id}/',
            action_label = 'Retry Payment',
            priority     = 'URGENT',
            related_obj  = payment,
        )


    @staticmethod
    def send_meet_link_set(appointment):
        """Patient notification when doctor sets Google Meet"""
        Notification.create_notification(
            recipient    = appointment.patient,
            notif_type   = 'MEET_LINK_SET',
            title        = '🎥 Meeting Link Ready',
            message      = (
                f'Dr. {appointment.doctor.get_full_name()} has set up your Google Meet session '
                f'for {appointment.appointment_date.strftime("%B %d")} '
                f'at {appointment.start_time.strftime("%I:%M %p")}. '
                f'Check your email for the meeting link.'
            ),
            action_url   = '/appointments/',
            action_label = 'View Meeting',
            priority     = 'HIGH',
            related_obj  = appointment,
        )


    @staticmethod
    def send_10min_reminder(appointment):
        """10-minute countdown reminder — to BOTH patient & doctor"""
        # Patient
        Notification.create_notification(
            recipient    = appointment.patient,
            notif_type   = 'REMINDER_10MIN',
            title        = '⏰ Your consultation starts in 10 minutes!',
            message      = (
                f'Dr. {appointment.doctor.get_full_name()} is preparing for your session. '
                f'Click below to join Google Meet now.'
            ),
            action_url   = appointment.meet_link or '/appointments/',
            action_label = 'Join Meeting',
            priority     = 'URGENT',
            related_obj  = appointment,
        )

        # Doctor
        Notification.create_notification(
            recipient    = appointment.doctor,
            notif_type   = 'REMINDER_10MIN',
            title        = '⏰ Consultation starts in 10 minutes',
            message      = (
                f'Patient {appointment.patient.get_full_name()} is awaiting your call. '
                f'Please join the Google Meet now.'
            ),
            action_url   = appointment.meet_link or '/appointments/',
            action_label = 'Open Meet',
            priority     = 'URGENT',
            related_obj  = appointment,
        )


    @staticmethod
    def send_record_available(record):
        Notification.create_notification(
            recipient    = record.patient,
            notif_type   = 'RECORD_AVAILABLE',
            title        = '📋 Your Medical Record is Ready',
            message      = (
                f'Dr. {record.doctor.get_full_name()} has finalized your consultation record. '
                f'You can now view your diagnosis, prescriptions, and follow-up notes.'
            ),
            action_url   = f'/records/{record.id}/',
            action_label = 'View Record',
            priority     = 'HIGH',
            related_obj  = record,
        )


    @staticmethod
    def broadcast_admin_notice(notice):
        """Send notice to all doctors"""
        from accounts.models import CustomUser
        doctors = CustomUser.objects.filter(role='DOCTOR', is_active=True)

        for doctor in doctors:
            Notification.create_notification(
                recipient    = doctor,
                notif_type   = 'ADMIN_NOTICE',
                title        = f'📢 {notice.title}',
                message      = notice.content,
                priority     = notice.priority if notice.priority in ['LOW','NORMAL','HIGH','URGENT'] else 'NORMAL',
                action_url   = '/dashboard/',
                action_label = 'View',
            )


    @staticmethod
    def send_email_with_log(subject, template_name, context, recipient_email, notification=None):
        """Send email + log it in EmailLog"""
        log_entry = EmailLog.objects.create(
            recipient_email      = recipient_email,
            subject              = subject,
            template             = template_name,
            related_notification = notification,
        )

        try:
            html = render_to_string(template_name, context)
            plain = f"{subject}\n\n{context.get('plain_message', '')}"

            msg = EmailMultiAlternatives(
                subject    = subject,
                body       = plain,
                from_email = settings.DEFAULT_FROM_EMAIL,
                to         = [recipient_email],
            )
            msg.attach_alternative(html, 'text/html')
            msg.send(fail_silently=False)

            log_entry.status   = 'SENT'
            log_entry.sent_at  = timezone.now()
            log_entry.attempts = 1
            log_entry.save()

            if notification:
                notification.email_sent    = True
                notification.email_sent_at = timezone.now()
                notification.save(update_fields=['email_sent', 'email_sent_at'])

            logger.info(f"Email sent: {subject} → {recipient_email}")
            return True

        except Exception as e:
            log_entry.status        = 'FAILED'
            log_entry.error_message = str(e)
            log_entry.attempts      = 1
            log_entry.save()

            logger.error(f"Email failed: {subject} → {recipient_email} | {e}")
            return False