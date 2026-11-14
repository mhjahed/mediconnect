# payments/models.py  — FULL Bangladesh Payment Model

import uuid
from django.db import models
from django.utils import timezone
from accounts.models import CustomUser


class PaymentRecord(models.Model):
    """
    Bangladesh-compatible payment tracking system.
    Supports: Bank Transfer, bKash, Nagad, Rocket, Cash, Other.
    Stripe / Card payments reserved for future production release.
    """

    PAYMENT_METHODS = [
        # ── Mobile Banking (Bangladesh) ──
        ('BKASH',   'bKash'),
        ('NAGAD',   'Nagad'),
        ('ROCKET',  'Rocket (DBBL)'),
        ('UPAY',    'Upay'),

        # ── Bank Transfer ──
        ('BANK_TRANSFER', 'Bank Transfer'),

        # ── Cash ──
        ('CASH', 'Cash Payment'),

        # ── Other ──
        ('OTHER', 'Other Payment Method'),

        # ── Future (disabled until production) ──
        # ('STRIPE',     'Stripe'),
        # ('MASTERCARD', 'Mastercard'),
        # ('VISA',       'Visa Card'),
    ]

    PAYMENT_STATUS = [
        ('PENDING',  'Pending Verification'),
        ('VERIFIED', 'Verified & Confirmed'),
        ('REJECTED', 'Rejected'),
        ('REFUNDED', 'Refunded'),
    ]

    # ── Core ──────────────────────────────────────────────
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment = models.OneToOneField(
        'appointments.Appointment',
        on_delete=models.CASCADE,
        related_name='payment_record'
    )
    patient     = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='payment_records',
        limit_choices_to={'role': 'PATIENT'}
    )
    amount      = models.DecimalField(max_digits=10, decimal_places=2)

    # ── Method ────────────────────────────────────────────
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='PENDING')

    # ── Bank Transfer fields ───────────────────────────────
    bank_name              = models.CharField(max_length=200, blank=True)
    bank_account_holder    = models.CharField(max_length=200, blank=True)
    bank_account_number    = models.CharField(max_length=100, blank=True)
    bank_transaction_id    = models.CharField(max_length=200, blank=True)
    bank_branch            = models.CharField(max_length=200, blank=True)

    # ── Mobile Banking fields (bKash / Nagad / Rocket / Upay) ──
    mobile_number          = models.CharField(max_length=20, blank=True)
    mobile_transaction_id  = models.CharField(max_length=200, blank=True)
    mobile_sender_number   = models.CharField(max_length=20, blank=True)

    # ── Other payment method ──────────────────────────────
    other_method_name      = models.CharField(max_length=200, blank=True)
    other_reference        = models.CharField(max_length=300, blank=True)

    # ── Shared notes ──────────────────────────────────────
    payment_notes          = models.TextField(blank=True)

    # ── Admin verification ────────────────────────────────
    verified_by            = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='verified_payments'
    )
    verified_at            = models.DateTimeField(null=True, blank=True)
    rejection_reason       = models.TextField(blank=True)

    # ── Timestamps ────────────────────────────────────────
    submitted_at           = models.DateTimeField(auto_now_add=True)
    updated_at             = models.DateTimeField(auto_now=True)

    # ── Future Stripe (reserved, not used yet) ────────────
    stripe_session_id      = models.CharField(max_length=300, blank=True)
    stripe_payment_id      = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering     = ['-submitted_at']
        verbose_name = 'Payment Record'

    def __str__(self):
        return (
            f"Payment #{str(self.id)[:8]} | "
            f"{self.get_payment_method_display()} | "
            f"৳{self.amount} | {self.payment_status}"
        )

    def get_reference_display(self):
        """Returns the main reference number based on payment method"""
        if self.payment_method == 'BANK_TRANSFER':
            return self.bank_transaction_id or '—'
        elif self.payment_method in ['BKASH', 'NAGAD', 'ROCKET', 'UPAY']:
            return self.mobile_transaction_id or '—'
        elif self.payment_method == 'OTHER':
            return self.other_reference or '—'
        return '—'

    def get_method_icon(self):
        icons = {
            'BKASH':         '📱',
            'NAGAD':         '📱',
            'ROCKET':        '📱',
            'UPAY':          '📱',
            'BANK_TRANSFER': '🏦',
            'CASH':          '💵',
            'OTHER':         '💳',
        }
        return icons.get(self.payment_method, '💳')