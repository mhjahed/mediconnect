# notifications/models.py

import uuid
from django.db import models
from django.utils import timezone
from accounts.models import CustomUser


class Notification(models.Model):
    """In-app notification system with bell icon support"""

    TYPE_CHOICES = [
        ('APPOINTMENT_CONFIRMED',  '✅ Appointment Confirmed'),
        ('PAYMENT_VERIFIED',       '💳 Payment Verified'),
        ('PAYMENT_REJECTED',       '❌ Payment Rejected'),
        ('MEET_LINK_SET',          '🎥 Meeting Link Available'),
        ('REMINDER_10MIN',         '⏰ 10-Minute Reminder'),
        ('REMINDER_24HR',          '📅 24-Hour Reminder'),
        ('RECORD_AVAILABLE',       '📋 Medical Record Available'),
        ('ADMIN_NOTICE',           '📢 Admin Notice'),
        ('SYSTEM_UPDATE',          '⚙️ System Update'),
        ('NEW_APPOINTMENT',        '📅 New Appointment Booked'),
        ('APPOINTMENT_CANCELLED',  '🚫 Appointment Cancelled'),
        ('ACCESS_GRANTED',         '🔓 Access Granted'),
        ('ACCESS_DENIED',          '🔒 Access Denied'),
        ('CUSTOM',                 '💬 General Notification'),
    ]

    PRIORITY = [
        ('LOW',      'Low'),
        ('NORMAL',   'Normal'),
        ('HIGH',     'High'),
        ('URGENT',   'Urgent'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient    = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=40, choices=TYPE_CHOICES, default='CUSTOM')
    priority     = models.CharField(max_length=10, choices=PRIORITY, default='NORMAL')

    # Content
    title        = models.CharField(max_length=200)
    message      = models.TextField()
    icon         = models.CharField(max_length=10, blank=True, default='🔔')

    # Optional action
    action_url   = models.URLField(max_length=500, blank=True)
    action_label = models.CharField(max_length=50, blank=True, default='View')

    # Related object (optional FK)
    related_object_id   = models.CharField(max_length=100, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)

    # Status
    is_read      = models.BooleanField(default=False)
    read_at      = models.DateTimeField(null=True, blank=True)

    # Email tracking
    email_sent   = models.BooleanField(default=False)
    email_sent_at= models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes  = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.icon} {self.title} → {self.recipient.email}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    @classmethod
    def create_notification(cls, recipient, notif_type, title, message,
                             icon=None, action_url='', action_label='View',
                             priority='NORMAL', related_obj=None,
                             send_email=False):
        """
        Helper to create notifications cleanly from anywhere.
        Auto-picks icon from type if not provided.
        """
        type_icons = {
            'APPOINTMENT_CONFIRMED': '✅',
            'PAYMENT_VERIFIED':      '💳',
            'PAYMENT_REJECTED':      '❌',
            'MEET_LINK_SET':         '🎥',
            'REMINDER_10MIN':        '⏰',
            'REMINDER_24HR':         '📅',
            'RECORD_AVAILABLE':      '📋',
            'ADMIN_NOTICE':          '📢',
            'NEW_APPOINTMENT':       '📅',
            'APPOINTMENT_CANCELLED': '🚫',
            'CUSTOM':                '🔔',
        }

        notif = cls.objects.create(
            recipient=recipient,
            notification_type=notif_type,
            title=title,
            message=message,
            icon=icon or type_icons.get(notif_type, '🔔'),
            action_url=action_url,
            action_label=action_label,
            priority=priority,
            related_object_id=str(related_obj.id) if related_obj else '',
            related_object_type=related_obj.__class__.__name__ if related_obj else '',
        )

        return notif


class EmailLog(models.Model):
    """Track all emails sent — for debugging and retry"""

    STATUS = [
        ('PENDING',  'Pending'),
        ('SENT',     'Sent Successfully'),
        ('FAILED',   'Failed'),
        ('RETRY',    'Will Retry'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient_email = models.EmailField()
    subject     = models.CharField(max_length=300)
    template    = models.CharField(max_length=100, blank=True)
    status      = models.CharField(max_length=20, choices=STATUS, default='PENDING')

    error_message = models.TextField(blank=True)
    attempts      = models.PositiveIntegerField(default=0)

    sent_at     = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    related_notification = models.ForeignKey(
        Notification, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='email_logs'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Email to {self.recipient_email} | {self.status}"