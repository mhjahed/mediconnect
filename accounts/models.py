# accounts/models.py — COMPLETE FILE

import uuid
import secrets
import string
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.conf import settings


# ══════════════════════════════════════════════════════════════
# USER MANAGER
# ══════════════════════════════════════════════════════════════
class CustomUserManager(BaseUserManager):
    """Manager for CustomUser model"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email address is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'ADMIN')
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email, password, **extra_fields)


# ══════════════════════════════════════════════════════════════
# CUSTOM USER
# ══════════════════════════════════════════════════════════════
class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Unified user model for Admin, Doctor, Nurse, Staff, Patient"""

    ROLE_CHOICES = [
        ('ADMIN',   'Super Admin'),
        ('DOCTOR',  'Doctor'),
        ('NURSE',   'Nurse'),
        ('STAFF',   'General Staff'),
        ('PATIENT', 'Patient'),
    ]

    GENDER_CHOICES = [
        ('MALE',   'Male'),
        ('FEMALE', 'Female'),
        ('OTHER',  'Other'),
    ]

    # ── Core Identity ─────────────────────────────────
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email        = models.EmailField(unique=True)
    username     = models.CharField(max_length=50, unique=True)
    first_name   = models.CharField(max_length=100)
    last_name    = models.CharField(max_length=100)
    role         = models.CharField(max_length=20, choices=ROLE_CHOICES, default='PATIENT')

    # ── Profile ───────────────────────────────────────
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    phone_number    = models.CharField(max_length=20, blank=True)
    gender          = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    date_of_birth   = models.DateField(null=True, blank=True)
    address         = models.TextField(blank=True)

    # ── System Flags ──────────────────────────────────
    is_active     = models.BooleanField(default=True)
    is_staff      = models.BooleanField(default=False)
    is_verified   = models.BooleanField(default=False)
    date_joined   = models.DateTimeField(default=timezone.now)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    objects = CustomUserManager()

    # ⬇️ THESE TWO LINES ARE CRITICAL — DO NOT REMOVE
    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name        = 'User'
        verbose_name_plural = 'Users'
        ordering            = ['-date_joined']

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    def is_doctor(self):
        return self.role == 'DOCTOR'

    def is_patient(self):
        return self.role == 'PATIENT'

    def is_admin(self):
        return self.role == 'ADMIN'

    def is_nurse(self):
        return self.role == 'NURSE'

    def is_staff_member(self):
        return self.role in ['NURSE', 'STAFF']

    def is_hospital_staff(self):
        """Any non-patient staff member"""
        return self.role in ['DOCTOR', 'NURSE', 'STAFF', 'ADMIN']

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"


# ══════════════════════════════════════════════════════════════
# DOCTOR PROFILE
# ══════════════════════════════════════════════════════════════
class DoctorProfile(models.Model):

    SPECIALTIES = [
        ('CARDIOLOGY',     'Cardiology'),
        ('NEUROLOGY',      'Neurology'),
        ('PEDIATRICS',     'Pediatrics'),
        ('ORTHOPEDICS',    'Orthopedics'),
        ('DERMATOLOGY',    'Dermatology'),
        ('PSYCHIATRY',     'Psychiatry'),
        ('ONCOLOGY',       'Oncology'),
        ('GYNECOLOGY',     'Gynecology'),
        ('OPHTHALMOLOGY',  'Ophthalmology'),
        ('DENTISTRY',      'Dentistry'),
        ('RADIOLOGY',      'Radiology'),
        ('EMERGENCY',      'Emergency Medicine'),
        ('GENERAL',        'General Practice'),
    ]

    user             = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='doctor_profile')
    specialty        = models.CharField(max_length=50, choices=SPECIALTIES)
    license_number   = models.CharField(max_length=100, unique=True)
    bio              = models.TextField(blank=True)
    years_experience = models.PositiveIntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    rating           = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    total_reviews    = models.PositiveIntegerField(default=0)
    education        = models.TextField(blank=True)
    languages        = models.CharField(max_length=200, default='English')
    is_available     = models.BooleanField(default=True)

    duty_start_time  = models.TimeField(null=True, blank=True)
    duty_end_time    = models.TimeField(null=True, blank=True)
    duty_days        = models.JSONField(default=list, help_text='e.g., ["MON","TUE","WED"]')

    class Meta:
        verbose_name = 'Doctor Profile'

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} – {self.specialty}"


# ══════════════════════════════════════════════════════════════
# PATIENT PROFILE
# ══════════════════════════════════════════════════════════════
class PatientProfile(models.Model):

    BLOOD_TYPES = [
        ('A+','A+'), ('A-','A-'), ('B+','B+'), ('B-','B-'),
        ('AB+','AB+'), ('AB-','AB-'), ('O+','O+'), ('O-','O-'),
    ]

    user                    = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='patient_profile')
    blood_type              = models.CharField(max_length=5, choices=BLOOD_TYPES, blank=True)
    medical_history         = models.TextField(blank=True)
    allergies               = models.TextField(blank=True)
    current_meds            = models.TextField(blank=True)
    emergency_contact_name  = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    insurance_provider      = models.CharField(max_length=100, blank=True)
    insurance_number        = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Patient Profile'

    def __str__(self):
        return f"Patient: {self.user.get_full_name()}"


# ══════════════════════════════════════════════════════════════
# STAFF PROFILE — Nurses, Ward Boys, IT, HR, etc.
# ══════════════════════════════════════════════════════════════
class StaffProfile(models.Model):

    STAFF_DEPARTMENTS = [
        ('NURSING',        '👩‍⚕️ Nursing'),
        ('WARD',           '🛏️ Ward Services'),
        ('PHARMACY_STAFF', '💊 Pharmacy Staff'),
        ('LAB_TECHNICIAN', '🔬 Laboratory Technician'),
        ('RADIOLOGY_TECH', '📡 Radiology Technician'),
        ('AMBULANCE',      '🚑 Ambulance Service'),
        ('HR',             '👥 Human Resources'),
        ('FINANCE',        '💰 Finance & Accounting'),
        ('MANAGEMENT',     '📊 Hospital Management'),
        ('RECEPTION',      '🏢 Reception & Front Desk'),
        ('PR_MARKETING',   '📢 PR & Marketing'),
        ('IT',             '💻 IT Department'),
        ('BIOMEDICAL',     '⚙️ Biomedical Engineering'),
        ('MAINTENANCE',    '🔧 Maintenance & Facilities'),
        ('SECURITY',       '🛡️ Security'),
        ('HOUSEKEEPING',   '🧹 Housekeeping'),
        ('CATERING',       '🍽️ Catering / Cafeteria'),
        ('LAUNDRY',        '👕 Laundry Services'),
        ('TRANSPORT',      '🚗 Transport & Logistics'),
        ('OTHER',          '📌 Other'),
    ]

    DESIGNATIONS = [
        ('CHIEF_NURSE',     'Chief Nurse'),
        ('HEAD_NURSE',      'Head Nurse'),
        ('SENIOR_NURSE',    'Senior Nurse'),
        ('STAFF_NURSE',     'Staff Nurse'),
        ('JUNIOR_NURSE',    'Junior Nurse'),
        ('TRAINEE_NURSE',   'Trainee Nurse'),
        ('MIDWIFE',         'Midwife'),
        ('ICU_NURSE',       'ICU Nurse'),
        ('OT_NURSE',        'OT Nurse'),
        ('WARD_BOY',        'Ward Boy / Attendant'),
        ('WARD_AYA',        'Ward Aya'),
        ('STRETCHER_BEARER','Stretcher Bearer'),
        ('PHARMACIST',      'Pharmacist'),
        ('ASST_PHARMACIST', 'Assistant Pharmacist'),
        ('LAB_TECH',        'Laboratory Technician'),
        ('LAB_ASSISTANT',   'Lab Assistant'),
        ('PATHOLOGIST',     'Pathologist'),
        ('RADIOLOGIST_TECH','Radiology Technician'),
        ('XRAY_TECH',       'X-Ray Technician'),
        ('SONOGRAPHER',     'Sonographer'),
        ('HR_MANAGER',      'HR Manager'),
        ('HR_EXECUTIVE',    'HR Executive'),
        ('ACCOUNTANT',      'Accountant'),
        ('FINANCE_HEAD',    'Finance Head'),
        ('GENERAL_MANAGER', 'General Manager'),
        ('OPERATIONS_MGR',  'Operations Manager'),
        ('RECEPTIONIST',    'Receptionist'),
        ('FRONT_DESK',      'Front Desk Officer'),
        ('ADMIN_OFFICER',   'Administrative Officer'),
        ('IT_MANAGER',      'IT Manager'),
        ('SYSTEM_ADMIN',    'System Administrator'),
        ('NETWORK_ENG',     'Network Engineer'),
        ('SOFTWARE_DEV',    'Software Developer'),
        ('IT_SUPPORT',      'IT Support Technician'),
        ('BIOMEDICAL_ENG',  'Biomedical Engineer'),
        ('ELECTRICIAN',     'Electrician'),
        ('PLUMBER',         'Plumber'),
        ('TECHNICIAN',      'General Technician'),
        ('SECURITY_HEAD',   'Security Head'),
        ('SECURITY_GUARD',  'Security Guard'),
        ('HOUSEKEEPING',    'Housekeeping Staff'),
        ('CLEANER',         'Cleaner'),
        ('CHEF',            'Chef / Cook'),
        ('CAFE_STAFF',      'Cafeteria Staff'),
        ('DRIVER',          'Driver'),
        ('AMBULANCE_DRIVER','Ambulance Driver'),
        ('CUSTOM',          'Other'),
    ]

    SHIFT_CHOICES = [
        ('MORNING',  '🌅 Morning Shift (6 AM - 2 PM)'),
        ('EVENING',  '🌆 Evening Shift (2 PM - 10 PM)'),
        ('NIGHT',    '🌙 Night Shift (10 PM - 6 AM)'),
        ('GENERAL',  '🏢 General Shift (9 AM - 5 PM)'),
        ('ROTATING', '🔄 Rotating Shift'),
        ('ON_CALL',  '📞 On Call'),
    ]

    user           = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE,
        related_name='staff_profile',
        limit_choices_to={'role__in': ['NURSE', 'STAFF']}
    )

    department         = models.CharField(max_length=50, choices=STAFF_DEPARTMENTS)
    designation        = models.CharField(max_length=50, choices=DESIGNATIONS)
    custom_designation = models.CharField(max_length=100, blank=True)
    employee_id        = models.CharField(max_length=50, unique=True, blank=True)

    date_of_joining = models.DateField(default=timezone.now)
    shift           = models.CharField(max_length=20, choices=SHIFT_CHOICES, default='GENERAL')
    salary          = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    supervisor      = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='supervised_staff'
    )

    is_active_employee = models.BooleanField(default=True)
    employment_type    = models.CharField(
        max_length=20,
        choices=[
            ('FULL_TIME',  'Full-Time'),
            ('PART_TIME',  'Part-Time'),
            ('CONTRACT',   'Contract'),
            ('INTERN',     'Intern'),
            ('VOLUNTEER',  'Volunteer'),
        ],
        default='FULL_TIME'
    )

    emergency_contact_name  = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_relation      = models.CharField(max_length=50, blank=True)

    notes      = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Staff Profile'
        verbose_name_plural = 'Staff Profiles'
        ordering = ['department', 'designation']

    def __str__(self):
        return f"{self.user.get_full_name()} – {self.get_designation_display()}"

    def get_display_designation(self):
        if self.designation == 'CUSTOM' and self.custom_designation:
            return self.custom_designation
        return self.get_designation_display()


# ══════════════════════════════════════════════════════════════
# DOCTOR ACCESS KEY
# ══════════════════════════════════════════════════════════════
class DoctorAccessKey(models.Model):

    STATUS_CHOICES = [
        ('ACTIVE',  'Active – Ready to Use'),
        ('USED',    'Used – Account Created'),
        ('REVOKED', 'Revoked – Deactivated'),
        ('EXPIRED', 'Expired'),
    ]

    key          = models.CharField(max_length=64, unique=True, editable=False)
    specialty    = models.CharField(max_length=50, choices=DoctorProfile.SPECIALTIES)
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    generated_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL,
        null=True, related_name='generated_keys',
        limit_choices_to={'role': 'ADMIN'}
    )
    used_by      = models.OneToOneField(
        CustomUser, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='used_key'
    )
    notes        = models.CharField(max_length=300, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    used_at      = models.DateTimeField(null=True, blank=True)
    expires_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Doctor Access Key'
        verbose_name_plural = 'Doctor Access Keys'
        ordering = ['-created_at']

    @classmethod
    def generate_key(cls):
        prefix = getattr(settings, 'ACCESS_KEY_PREFIX', 'MEDI')
        chars = string.ascii_uppercase + string.digits
        parts = [''.join(secrets.choice(chars) for _ in range(4)) for _ in range(3)]
        return f"{prefix}-{parts[0]}-{parts[1]}-{parts[2]}"

    def mark_used(self, user):
        self.status = 'USED'
        self.used_by = user
        self.used_at = timezone.now()
        self.save()

    def is_valid(self):
        if self.status != 'ACTIVE':
            return False, 'This key has already been used or revoked.'
        if self.expires_at and timezone.now() > self.expires_at:
            self.status = 'EXPIRED'
            self.save()
            return False, 'This key has expired.'
        return True, 'Valid'

    def __str__(self):
        return f"{self.key} ({self.specialty}) – {self.status}"


# ══════════════════════════════════════════════════════════════
# STAFF ACCESS KEY — For Nurses, Ward Boys, IT, HR, etc.
# ══════════════════════════════════════════════════════════════
class StaffAccessKey(models.Model):

    STATUS_CHOICES = [
        ('ACTIVE',  'Active – Ready to Use'),
        ('USED',    'Used – Account Created'),
        ('REVOKED', 'Revoked – Deactivated'),
        ('EXPIRED', 'Expired'),
    ]

    ROLE_CHOICES = [
        ('NURSE', 'Nurse'),
        ('STAFF', 'General Staff'),
    ]

    key          = models.CharField(max_length=64, unique=True, editable=False)
    role         = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STAFF')
    department   = models.CharField(max_length=50, choices=StaffProfile.STAFF_DEPARTMENTS)
    designation  = models.CharField(max_length=50, choices=StaffProfile.DESIGNATIONS)
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    generated_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL,
        null=True, related_name='generated_staff_keys',
        limit_choices_to={'role': 'ADMIN'}
    )
    used_by      = models.OneToOneField(
        CustomUser, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='used_staff_key'
    )
    notes        = models.CharField(max_length=300, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    used_at      = models.DateTimeField(null=True, blank=True)
    expires_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Staff Access Key'
        verbose_name_plural = 'Staff Access Keys'
        ordering = ['-created_at']

    @classmethod
    def generate_key(cls):
        chars = string.ascii_uppercase + string.digits
        parts = [''.join(secrets.choice(chars) for _ in range(4)) for _ in range(3)]
        return f"STAFF-{parts[0]}-{parts[1]}-{parts[2]}"

    def mark_used(self, user):
        self.status = 'USED'
        self.used_by = user
        self.used_at = timezone.now()
        self.save()

    def is_valid(self):
        if self.status != 'ACTIVE':
            return False, 'This key has already been used or revoked.'
        if self.expires_at and timezone.now() > self.expires_at:
            self.status = 'EXPIRED'
            self.save()
            return False, 'This key has expired.'
        return True, 'Valid'

    def __str__(self):
        return f"{self.key} ({self.get_role_display()}) – {self.status}"


# ══════════════════════════════════════════════════════════════
# DOCTOR ATTENDANCE
# ══════════════════════════════════════════════════════════════
class DoctorAttendance(models.Model):

    doctor   = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date     = models.DateField(default=timezone.now)
    time_in  = models.TimeField(auto_now_add=True)
    time_out = models.TimeField(null=True, blank=True)
    status   = models.CharField(
        max_length=20,
        choices=[('PRESENT','Present'), ('LATE','Late'), ('HALF_DAY','Half Day')],
        default='PRESENT'
    )
    notes    = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Doctor Attendance'
        verbose_name_plural = 'Doctor Attendance Records'
        unique_together = ['doctor', 'date']
        ordering = ['-date']

    @classmethod
    def has_marked_today(cls, doctor):
        today = timezone.now().date()
        return cls.objects.filter(doctor=doctor, date=today).exists()

    def __str__(self):
        return f"Dr. {self.doctor.get_full_name()} – {self.date} ({self.status})"


# ══════════════════════════════════════════════════════════════
# ADMIN NOTICE
# ══════════════════════════════════════════════════════════════
class AdminNotice(models.Model):

    PRIORITY_CHOICES = [
        ('LOW',      'Low'),
        ('NORMAL',   'Normal'),
        ('HIGH',     'High'),
        ('CRITICAL', 'Critical'),
    ]

    title      = models.CharField(max_length=200)
    content    = models.TextField()
    priority   = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='NORMAL')
    posted_by  = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.priority}] {self.title}"