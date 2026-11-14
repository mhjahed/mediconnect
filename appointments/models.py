# appointments/models.py  — COMPLETE FIXED FILE

import uuid
from django.db import models
from django.utils import timezone
from accounts.models import CustomUser


class Appointment(models.Model):

    STATUS_CHOICES = [
        ('PENDING',    'Pending Payment'),
        ('CONFIRMED',  'Confirmed'),
        ('MEET_SET',   'Meeting Link Set'),
        ('COMPLETED',  'Completed'),
        ('CANCELLED',  'Cancelled'),
        ('NO_SHOW',    'No Show'),
    ]

    PAYMENT_STATUS = [
        ('UNPAID',    'Unpaid'),
        ('PAID',      'Paid'),
        ('REFUNDED',  'Refunded'),
        ('FAILED',    'Failed'),
    ]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient          = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name='patient_appointments',
        limit_choices_to={'role': 'PATIENT'}
    )
    doctor           = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name='doctor_appointments',
        limit_choices_to={'role': 'DOCTOR'}
    )
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # Scheduling
    appointment_date = models.DateField()
    start_time       = models.TimeField()
    end_time         = models.TimeField()

    # Google Meet
    meet_link        = models.URLField(max_length=500, blank=True, default='')
    meeting_time     = models.DateTimeField(null=True, blank=True)
    meet_notes       = models.TextField(blank=True)

    # Payment
    amount           = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status   = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='UNPAID')

    # Stripe fields (kept for future production use — currently unused)
    stripe_session_id = models.CharField(max_length=300, blank=True)
    stripe_payment_id = models.CharField(max_length=300, blank=True)

    # Reminders
    reminder_10min_sent = models.BooleanField(default=False)
    confirmation_sent   = models.BooleanField(default=False)

    # Meta
    chief_complaint  = models.TextField(blank=True)
    booked_at        = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering   = ['-appointment_date', '-start_time']
        verbose_name = 'Appointment'

    def __str__(self):
        return (
            f"#{str(self.id)[:8]} | "
            f"Dr.{self.doctor.get_full_name()} ← {self.patient.get_full_name()} "
            f"| {self.appointment_date}"
        )

    def get_meeting_datetime(self):
        return timezone.datetime.combine(
            self.appointment_date,
            self.start_time,
            tzinfo=timezone.get_current_timezone()
        )

    def is_upcoming(self):
        return self.get_meeting_datetime() > timezone.now()

    def minutes_until(self):
        delta = self.get_meeting_datetime() - timezone.now()
        return int(delta.total_seconds() / 60)


class DoctorReview(models.Model):
    """Patient reviews for doctors"""

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='review'
    )
    # ── FIX: unique related_name for each FK ──────────────
    patient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='reviews_given',          # ← FIXED
        limit_choices_to={'role': 'PATIENT'}
    )
    doctor  = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='reviews_received',       # ← FIXED
        limit_choices_to={'role': 'DOCTOR'}
    )
    rating     = models.PositiveIntegerField(default=5)
    comment    = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return (
            f"{self.patient.get_full_name()} → "
            f"Dr.{self.doctor.get_full_name()} ({self.rating}★)"
        )