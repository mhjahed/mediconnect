# medical_records/models.py

import uuid
from django.db import models
from django.utils import timezone
from accounts.models import CustomUser
from appointments.models import Appointment


class MedicalRecord(models.Model):
    """
    Created by doctor after each consultation.
    Patient can view/download after payment is verified.
    """

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='medical_record'
    )
    patient     = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='medical_records',
        limit_choices_to={'role': 'PATIENT'}
    )
    doctor      = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='doctor_records',
        limit_choices_to={'role': 'DOCTOR'}
    )

    # ── Consultation details ──────────────────────────────
    chief_complaint      = models.TextField(blank=True)
    history_of_illness   = models.TextField(blank=True, verbose_name='History of Present Illness')
    examination_findings = models.TextField(blank=True, verbose_name='Physical Examination Findings')
    diagnosis            = models.TextField(verbose_name='Diagnosis / Impression')
    treatment_plan       = models.TextField(blank=True, verbose_name='Treatment Plan')
    follow_up_notes      = models.TextField(blank=True, verbose_name='Follow-up Instructions')

    # ── Vitals ───────────────────────────────────────────
    blood_pressure    = models.CharField(max_length=20, blank=True, help_text='e.g. 120/80 mmHg')
    pulse_rate        = models.CharField(max_length=20, blank=True, help_text='e.g. 72 bpm')
    temperature       = models.CharField(max_length=20, blank=True, help_text='e.g. 98.6°F')
    weight            = models.CharField(max_length=20, blank=True, help_text='e.g. 70 kg')
    oxygen_saturation = models.CharField(max_length=20, blank=True, help_text='e.g. 98%')

    # ── Status ───────────────────────────────────────────
    is_finalized = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Record: {self.patient.get_full_name()} | Dr.{self.doctor.get_full_name()} | {self.created_at.date()}"

    def has_access(self, user):
        """Check if user can view this record"""
        if user.is_superuser or user.role == 'ADMIN':
            return True
        if user.role == 'DOCTOR' and user == self.doctor:
            return True
        if user.role == 'PATIENT' and user == self.patient:
            # Patient can only view if appointment is PAID
            return self.appointment.payment_status == 'PAID'
        return False


class Prescription(models.Model):
    """Medications prescribed in a consultation"""

    FREQUENCY_CHOICES = [
        ('OD',    'Once Daily (OD)'),
        ('BD',    'Twice Daily (BD)'),
        ('TDS',   'Three Times Daily (TDS)'),
        ('QDS',   'Four Times Daily (QDS)'),
        ('SOS',   'As Needed (SOS)'),
        ('STAT',  'Immediately (STAT)'),
        ('OW',    'Once Weekly (OW)'),
        ('ON',    'At Night (ON)'),
        ('OM',    'In the Morning (OM)'),
    ]

    DURATION_UNITS = [
        ('DAYS',   'Days'),
        ('WEEKS',  'Weeks'),
        ('MONTHS', 'Months'),
    ]

    ROUTE_CHOICES = [
        ('ORAL',        'Oral'),
        ('IV',          'Intravenous (IV)'),
        ('IM',          'Intramuscular (IM)'),
        ('SC',          'Subcutaneous (SC)'),
        ('TOPICAL',     'Topical'),
        ('INHALED',     'Inhaled'),
        ('SUBLINGUAL',  'Sublingual'),
        ('RECTAL',      'Rectal'),
        ('OPHTHALMIC',  'Eye Drops'),
        ('NASAL',       'Nasal'),
    ]

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )

    # ── Drug info ─────────────────────────────────────────
    drug_name    = models.CharField(max_length=300)
    generic_name = models.CharField(max_length=300, blank=True)
    dosage       = models.CharField(max_length=100, help_text='e.g. 500mg, 10mg/5ml')
    frequency    = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    route        = models.CharField(max_length=20, choices=ROUTE_CHOICES, default='ORAL')
    duration     = models.PositiveIntegerField(default=7)
    duration_unit= models.CharField(max_length=10, choices=DURATION_UNITS, default='DAYS')
    instructions = models.TextField(blank=True, help_text='e.g. Take with food, avoid alcohol')
    quantity     = models.CharField(max_length=50, blank=True, help_text='Total quantity to dispense')

    order_number = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order_number']

    def __str__(self):
        return f"{self.drug_name} {self.dosage} — {self.get_frequency_display()}"

    def get_duration_display_str(self):
        return f"{self.duration} {self.get_duration_unit_display()}"


class LabTest(models.Model):
    """Lab investigations ordered during consultation"""

    URGENCY = [
        ('ROUTINE',  'Routine'),
        ('URGENT',   'Urgent'),
        ('STAT',     'STAT (Immediate)'),
    ]

    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='lab_tests')
    test_name      = models.CharField(max_length=300)
    urgency        = models.CharField(max_length=10, choices=URGENCY, default='ROUTINE')
    instructions   = models.CharField(max_length=500, blank=True)
    result         = models.TextField(blank=True)
    result_date    = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.test_name} [{self.urgency}]"