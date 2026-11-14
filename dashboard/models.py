# dashboard/models.py

from django.db import models
from django.utils import timezone
from accounts.models import CustomUser


class DoctorSchedule(models.Model):
    """Weekly availability schedule for doctors"""

    DAY_CHOICES = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday'),
    ]

    doctor          = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='schedules', limit_choices_to={'role': 'DOCTOR'})
    day_of_week     = models.CharField(max_length=3, choices=DAY_CHOICES)
    start_time      = models.TimeField()
    end_time        = models.TimeField()
    slot_duration   = models.PositiveIntegerField(default=30, help_text='Duration of each slot in minutes')
    is_available    = models.BooleanField(default=True)
    effective_from  = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ['doctor', 'day_of_week', 'effective_from']
        ordering = ['day_of_week']

    def __str__(self):
        return f"Dr. {self.doctor.get_full_name()} – {self.day_of_week} {self.start_time}–{self.end_time}"