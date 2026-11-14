# notifications/management/commands/send_reminders.py

import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger('mediconnect')


class Command(BaseCommand):
    help = 'Sends 10-minute reminders for upcoming appointments + creates in-app notifications'

    def handle(self, *args, **options):
        from appointments.models import Appointment
        from notifications.services import NotificationService
        from notifications.email_service import send_reminder_email

        now = timezone.now()
        window_start = now + timedelta(minutes=9, seconds=30)
        window_end   = now + timedelta(minutes=10, seconds=30)

        # Find appointments starting in ~10 minutes
        upcoming = Appointment.objects.filter(
            status='MEET_SET',
            payment_status='PAID',
            reminder_10min_sent=False,
            meeting_time__gte=window_start,
            meeting_time__lte=window_end,
        ).select_related('doctor', 'patient', 'doctor__doctor_profile')

        if not upcoming.exists():
            self.stdout.write('No reminders to send.')
            return

        sent_count = 0
        for appt in upcoming:
            try:
                # 1. Create in-app notifications
                NotificationService.send_10min_reminder(appt)

                # 2. Send email reminders
                send_reminder_email(appt)

                # 3. Mark as sent
                appt.reminder_10min_sent = True
                appt.save(update_fields=['reminder_10min_sent'])

                sent_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Reminder sent: {appt.patient.get_full_name()} → "
                    f"Dr. {appt.doctor.get_full_name()}"
                ))

            except Exception as e:
                logger.error(f"Reminder failed for {appt.id}: {e}")
                self.stdout.write(self.style.ERROR(f"❌ {appt.id}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\n📊 Total reminders sent: {sent_count}"))