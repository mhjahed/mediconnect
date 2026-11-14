# access_control/models.py
import secrets
import string
import uuid
import logging
from django.db import models
from django.utils import timezone
from django.conf import settings
import os

logger = logging.getLogger('mediconnect')


class AccessZone(models.Model):
    """Rooms/areas in the hospital that require barcode scan to enter"""

    ZONE_TYPES = [
        ('STORAGE',        '🗄️ Storage Room'),
        ('SURGERY',        '🏥 Surgery Room'),
        ('MEDICINE',       '💊 Medicine Room'),
        ('INVENTORY',      '📦 Inventory Room'),
        ('COMMON',         '🪑 Common Room'),
        ('DOCTOR_ROOM',    '👨‍⚕️ Doctor\'s Room'),
        ('CAFE',           '☕ Café'),
        ('STAFF_COMMON',   '🛋️ Staff Common Room'),
        ('NURSE_ROOM',     '👩‍⚕️ Nurse Room'),
        ('LAB',            '🔬 Laboratory'),
        ('RADIOLOGY',      '📡 Radiology'),
        ('ICU',            '🚨 ICU'),
        ('EMERGENCY',      '🚑 Emergency Room'),
        ('PHARMACY',       '💉 Pharmacy'),
        ('RECEPTION',      '🏢 Reception'),
        ('ADMIN_OFFICE',   '🛡️ Admin Office'),
        ('RECORDS_ROOM',   '📋 Records Room'),
        ('CONSULTATION',   '🩺 Consultation Room'),
        ('WAITING_AREA',   '⏳ Waiting Area'),
        ('MAINTENANCE',    '🔧 Maintenance Room'),
    ]

    ALLOWED_ROLE_CHOICES = [
        ('ALL',     'All Staff'),
        ('DOCTOR',  'Doctors Only'),
        ('ADMIN',   'Admins Only'),
        ('NURSE',   'Nurses Only'),
        ('STAFF',   'General Staff'),
    ]

    zone_id      = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name         = models.CharField(max_length=200)
    zone_type    = models.CharField(max_length=30, choices=ZONE_TYPES)
    description  = models.TextField(blank=True)
    floor_number = models.IntegerField(default=1)
    room_number  = models.CharField(max_length=30, blank=True)

    # The barcode/QR text that grants access to this zone
    access_code_text = models.CharField(
        max_length=500,
        unique=True,
        help_text="Exact text encoded in the barcode/QR posted on the door."
    )

    # Who can enter
    allowed_roles = models.JSONField(
        default=list,
        help_text='e.g., ["DOCTOR", "ADMIN", "NURSE"]'
    )

    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['floor_number', 'name']

    def __str__(self):
        return f"{self.get_zone_type_display()} – {self.name} (Floor {self.floor_number})"

    def get_icon(self):
        icons = dict(self.ZONE_TYPES)
        return icons.get(self.zone_type, '🚪').split(' ')[0]


class BarcodeAccessLog(models.Model):
    """Every single scan attempt — success or failure"""

    RESULTS = [
        ('GRANTED',           '✅ Access Granted'),
        ('DENIED',            '❌ Access Denied'),
        ('UNKNOWN_CODE',      '❓ Unknown Barcode'),
        ('INACTIVE_ZONE',     '🔒 Zone Inactive'),
        ('UNAUTHORIZED_ROLE', '🚫 Unauthorized Role'),
        ('NOT_LOGGED_IN',     '🔑 Not Logged In'),
        ('SCAN_ERROR',        '⚠️ Scan Error'),
    ]

    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='access_logs'
    )
    zone = models.ForeignKey(
        AccessZone,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='access_logs'
    )

    scanned_text   = models.TextField(help_text="Raw text from barcode/QR")
    barcode_format = models.CharField(max_length=50, blank=True, default='unknown')
    access_result  = models.CharField(max_length=30, choices=RESULTS)
    room_selected  = models.CharField(max_length=200, blank=True)
    timestamp      = models.DateTimeField(auto_now_add=True)
    ip_address     = models.GenericIPAddressField(null=True, blank=True)
    device_info    = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        user_str = self.user.get_full_name() if self.user else "Unknown"
        return f"{user_str} → {self.access_result} | {self.timestamp}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Also write to log file
        _write_to_log_file(self)


class PersonalAccessBarcode(models.Model):
    """Each staff member's personal ID badge barcode"""

    user = models.OneToOneField(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='access_barcode'
    )
    barcode_text  = models.CharField(max_length=500, unique=True)
    barcode_image = models.ImageField(upload_to='qr_codes/', null=True, blank=True)
    is_active     = models.BooleanField(default=True)
    issued_at     = models.DateTimeField(auto_now_add=True)
    expires_at    = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Badge: {self.user.get_full_name()}"

    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


def _write_to_log_file(log_entry):
    """Writes every scan attempt to logs/access_log.txt automatically"""
    try:
        log_dir  = settings.BASE_DIR / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'access_log.txt'

        user_name = log_entry.user.get_full_name() if log_entry.user else 'UNKNOWN_USER'
        user_role = log_entry.user.role if log_entry.user else 'N/A'
        zone_name = log_entry.zone.name if log_entry.zone else 'N/A'
        zone_type = log_entry.zone.get_zone_type_display() if log_entry.zone else 'N/A'

        timestamp = log_entry.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log_entry.timestamp else timezone.now().strftime('%Y-%m-%d %H:%M:%S')

        # Build log line
        result_icon = dict(BarcodeAccessLog.RESULTS).get(log_entry.access_result, '')

        line = (
            f"[{timestamp}] "
            f"{result_icon} | "
            f"Result: {log_entry.access_result:20s} | "
            f"User: {user_name:25s} | "
            f"Role: {user_role:10s} | "
            f"Zone: {zone_name:25s} | "
            f"Room Type: {zone_type:25s} | "
            f"Barcode Text: {log_entry.scanned_text[:50]:50s} | "
            f"Format: {log_entry.barcode_format:15s} | "
            f"IP: {log_entry.ip_address or 'N/A':15s} | "
            f"Device: {log_entry.device_info[:60]}\n"
        )

        # Append to file
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(line)

        # Also write errors to separate error log
        if log_entry.access_result in ['DENIED', 'UNKNOWN_CODE', 'UNAUTHORIZED_ROLE', 'SCAN_ERROR', 'NOT_LOGGED_IN']:
            error_file = log_dir / 'access_errors.txt'
            with open(error_file, 'a', encoding='utf-8') as f:
                f.write(f"[ERROR] {line}")

    except Exception as e:
        logger.error(f"Failed to write access log file: {e}")

import secrets
import string
import os
from io import BytesIO
from django.core.files.base import ContentFile
class StaffIDCard(models.Model):
    """ID Card with optimized short barcodes for quick scanning"""

    CARD_STATUS = [
        ('ACTIVE',  '🟢 Active'),
        ('EXPIRED', '🔴 Expired'),
        ('REVOKED', '⛔ Revoked'),
        ('LOST',    '⚠️ Reported Lost'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user            = models.OneToOneField(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='id_card'
    )

    staff_id_number = models.CharField(max_length=20, unique=True)
    access_code     = models.CharField(
        max_length=20,                          # ⬅ REDUCED from 50 to 20
        unique=True,
        help_text='Short barcode-friendly access code (12 chars)'
    )

    # Barcode image — auto-generated
    barcode_image   = models.ImageField(
        upload_to='barcodes/',
        null=True, blank=True,
        help_text='Auto-generated Code 128 barcode'
    )

    designation     = models.CharField(max_length=100)
    department      = models.CharField(max_length=100, blank=True)
    desk_number     = models.CharField(max_length=50, blank=True)
    blood_group     = models.CharField(max_length=10, blank=True)

    allowed_zones   = models.ManyToManyField(
        AccessZone,
        related_name='authorized_cards',
        blank=True
    )

    issue_date      = models.DateField(default=timezone.now)
    valid_till      = models.DateField()

    status          = models.CharField(max_length=20, choices=CARD_STATUS, default='ACTIVE')
    issued_by       = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='issued_cards'
    )
    created_at      = models.DateTimeField(auto_now_add=True)
    notes           = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Staff ID Card'

    def __str__(self):
        return f"ID #{self.staff_id_number} — {self.user.get_full_name()}"

    @classmethod
    def generate_staff_id(cls):
        """Generate unique 8-digit numeric ID"""
        while True:
            num = ''.join(secrets.choice(string.digits) for _ in range(8))
            if not cls.objects.filter(staff_id_number=num).exists():
                return num

    @classmethod
    def generate_access_code(cls, user):
        """
        Generate SHORT scanner-friendly access code.

        Format: MEDI-XXX-NNNN (12 chars total)
          MEDI = prefix
          XXX  = role short (DOC, NUR, STA, ADM)
          NNNN = 4-char random uppercase + digits

        Example: MEDI-DOC-A7K3, MEDI-NUR-B2P9
        """
        role_map = {
            'DOCTOR': 'DOC',
            'NURSE':  'NUR',
            'STAFF':  'STA',
            'ADMIN':  'ADM',
        }
        role_short = role_map.get(user.role, 'STA')

        # Generate unique 4-char suffix (uppercase + digits only - best for Code128)
        chars = string.ascii_uppercase + string.digits
        max_attempts = 50

        for _ in range(max_attempts):
            suffix = ''.join(secrets.choice(chars) for _ in range(4))
            code = f"MEDI-{role_short}-{suffix}"
            if not cls.objects.filter(access_code=code).exists():
                return code

        # Fallback with 5 chars if 4-char collision (extremely rare)
        suffix = ''.join(secrets.choice(chars) for _ in range(5))
        return f"MEDI-{role_short}-{suffix}"

    def generate_barcode_image(self):
        """
        Generates Code 128 barcode PNG image from access_code.
        Optimized for fast scanning.
        """
        try:
            from barcode import Code128
            from barcode.writer import ImageWriter

            # Code 128 — best format for alphanumeric short codes
            writer_options = {
                'module_width':   0.4,    # bar width (mm)
                'module_height':  15.0,   # bar height (mm)
                'quiet_zone':     6.0,    # white space around (mm)
                'font_size':      11,     # text below
                'text_distance':  5.0,    # gap between bars and text
                'background':     'white',
                'foreground':     'black',
                'write_text':     True,
                'dpi':            300,
            }

            buffer = BytesIO()
            barcode_obj = Code128(self.access_code, writer=ImageWriter())
            barcode_obj.write(buffer, options=writer_options)

            # Save to image field
            filename = f"barcode_{self.staff_id_number}.png"
            self.barcode_image.save(
                filename,
                ContentFile(buffer.getvalue()),
                save=False
            )
            return True

        except ImportError:
            print("⚠️ Install python-barcode: pip install python-barcode pillow")
            return False
        except Exception as e:
            print(f"❌ Barcode generation failed: {e}")
            return False

    def save(self, *args, **kwargs):
        # Auto-generate barcode on first save
        if not self.barcode_image and self.access_code:
            self.generate_barcode_image()
        super().save(*args, **kwargs)

    def is_valid(self):
        if self.status != 'ACTIVE':
            return False
        if timezone.now().date() > self.valid_till:
            return False
        return True

    def days_until_expiry(self):
        delta = self.valid_till - timezone.now().date()
        return delta.days