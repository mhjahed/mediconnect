
import stripe
import json
import logging

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils import timezone

from appointments.models import Appointment
from .models import PaymentRecord
from .forms import BankTransferForm, MobileBankingForm, OtherPaymentForm

# ⬇️ ADD THIS IMPORT — fixes the NameError
from dashboard.admin_views import admin_required

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger('mediconnect')

# ══════════════════════════════════════════════════════════════
# PAYMENT HUB — Choose payment method
# ══════════════════════════════════════════════════════════════
@login_required
def checkout_view(request, appointment_id):
    """
    Landing page for payment.
    Patient selects their payment method from available options.
    """
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient=request.user,
        payment_status='UNPAID',
    )

    try:
        specialty = appointment.doctor.doctor_profile.get_specialty_display()
    except Exception:
        specialty = 'Consultation'

    # Our payment receiving details (displayed to patient)
    payment_info = {
        'bkash_number':   '01XXXXXXXXX',   # ← Replace with real number
        'nagad_number':   '01XXXXXXXXX',
        'rocket_number':  '01XXXXXXXXX',
        'bank_name':      'Dutch-Bangla Bank Ltd.',
        'bank_account':   'XXXX-XXXX-XXXX',
        'bank_holder':    'MediConnect Healthcare Ltd.',
        'bank_branch':    'Dhaka Main Branch',
        'bank_routing':   '090261XXX',
    }

    return render(request, 'payments/checkout.html', {
        'appointment':  appointment,
        'specialty':    specialty,
        'payment_info': payment_info,
    })


# ══════════════════════════════════════════════════════════════
# SUBMIT BANK TRANSFER
# ══════════════════════════════════════════════════════════════
@login_required
@require_http_methods(['POST'])
def submit_bank_transfer(request, appointment_id):
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient=request.user,
        payment_status='UNPAID',
    )

    form = BankTransferForm(request.POST)
    if form.is_valid():
        record = form.save(commit=False)
        record.appointment     = appointment
        record.patient         = request.user
        record.amount          = appointment.amount
        record.payment_method  = 'BANK_TRANSFER'
        record.payment_status  = 'PENDING'
        record.save()

        # Mark appointment as pending verification
        appointment.payment_status = 'UNPAID'
        appointment.status         = 'PENDING'
        appointment.save(update_fields=['payment_status', 'status'])

        logger.info(
            f"Bank transfer submitted | "
            f"Appointment: {appointment_id} | "
            f"TXN: {record.bank_transaction_id}"
        )

        return redirect('payments:pending', payment_id=record.id)

    # Form errors — re-render checkout with errors
    messages.error(request, 'Please fill in all required payment details.')
    return redirect('payments:checkout', appointment_id=appointment_id)


# ══════════════════════════════════════════════════════════════
# SUBMIT MOBILE BANKING (bKash / Nagad / Rocket / Upay)
# ══════════════════════════════════════════════════════════════
@login_required
@require_http_methods(['POST'])
def submit_mobile_banking(request, appointment_id):
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient=request.user,
        payment_status='UNPAID',
    )

    method = request.POST.get('mobile_method', 'BKASH').upper()
    if method not in ['BKASH', 'NAGAD', 'ROCKET', 'UPAY']:
        method = 'BKASH'

    form = MobileBankingForm(request.POST)
    if form.is_valid():
        record = form.save(commit=False)
        record.appointment    = appointment
        record.patient        = request.user
        record.amount         = appointment.amount
        record.payment_method = method
        record.payment_status = 'PENDING'
        record.save()

        appointment.payment_status = 'UNPAID'
        appointment.status         = 'PENDING'
        appointment.save(update_fields=['payment_status', 'status'])

        logger.info(
            f"{method} payment submitted | "
            f"Appointment: {appointment_id} | "
            f"TXN: {record.mobile_transaction_id}"
        )

        return redirect('payments:pending', payment_id=record.id)

    messages.error(request, 'Please fill in all required payment details.')
    return redirect('payments:checkout', appointment_id=appointment_id)


# ══════════════════════════════════════════════════════════════
# SUBMIT OTHER PAYMENT
# ══════════════════════════════════════════════════════════════
@login_required
@require_http_methods(['POST'])
def submit_other_payment(request, appointment_id):
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient=request.user,
        payment_status='UNPAID',
    )

    form = OtherPaymentForm(request.POST)
    if form.is_valid():
        record = form.save(commit=False)
        record.appointment    = appointment
        record.patient        = request.user
        record.amount         = appointment.amount
        record.payment_method = 'OTHER'
        record.payment_status = 'PENDING'
        record.save()

        appointment.payment_status = 'UNPAID'
        appointment.status         = 'PENDING'
        appointment.save(update_fields=['payment_status', 'status'])

        return redirect('payments:pending', payment_id=record.id)

    messages.error(request, 'Please fill in all required details.')
    return redirect('payments:checkout', appointment_id=appointment_id)


# ══════════════════════════════════════════════════════════════
# PAYMENT PENDING — Awaiting admin verification
# ══════════════════════════════════════════════════════════════
@login_required
def payment_pending(request, payment_id):
    payment = get_object_or_404(
        PaymentRecord,
        id=payment_id,
        patient=request.user,
    )
    return render(request, 'payments/pending.html', {
        'payment':     payment,
        'appointment': payment.appointment,
    })


# ══════════════════════════════════════════════════════════════
# PAYMENT SUCCESS (after admin verifies)
# ══════════════════════════════════════════════════════════════
@login_required
def payment_success(request):
    appointment_id = request.GET.get('appointment_id')
    appointment    = None

    if appointment_id:
        try:
            appointment = Appointment.objects.get(
                id=appointment_id,
                patient=request.user
            )
        except Appointment.DoesNotExist:
            pass

    return render(request, 'payments/success.html', {
        'appointment': appointment,
    })


# ══════════════════════════════════════════════════════════════
# PAYMENT FAILED / CANCELLED
# ══════════════════════════════════════════════════════════════
@login_required
def payment_failed(request):
    appointment_id = request.GET.get('appointment_id')
    appointment    = None

    if appointment_id:
        try:
            appointment = Appointment.objects.get(
                id=appointment_id,
                patient=request.user
            )
        except Appointment.DoesNotExist:
            pass

    return render(request, 'payments/failed.html', {
        'appointment': appointment,
    })


# ══════════════════════════════════════════════════════════════
# ADMIN — VERIFY PAYMENT
# ══════════════════════════════════════════════════════════════

@login_required
@admin_required
def verify_payment(request, payment_id):
    from notifications.services import NotificationService

    payment = get_object_or_404(PaymentRecord, id=payment_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'verify':
            payment.payment_status = 'VERIFIED'
            payment.verified_by    = request.user
            payment.verified_at    = timezone.now()
            payment.save()

            payment.appointment.payment_status = 'PAID'
            payment.appointment.status         = 'CONFIRMED'
            payment.appointment.save(update_fields=['payment_status', 'status'])

            # 🔔 Send notifications
            NotificationService.send_appointment_confirmed(payment.appointment)

            messages.success(request, f'✅ Payment verified for {payment.patient.get_full_name()}')

        elif action == 'reject':
            reason = request.POST.get('rejection_reason', 'Could not verify payment.')
            payment.payment_status   = 'REJECTED'
            payment.rejection_reason = reason
            payment.save()

            # 🔔 Notify patient
            NotificationService.send_payment_rejected(payment, reason)

            messages.warning(request, f'❌ Payment rejected for {payment.patient.get_full_name()}')

    return redirect('dashboard:admin_payments')

# ══════════════════════════════════════════════════════════════
# ADMIN — LIST ALL PENDING PAYMENTS
# ══════════════════════════════════════════════════════════════
@login_required
def admin_payment_list(request):
    if not request.user.is_superuser and request.user.role != 'ADMIN':
        messages.error(request, 'Unauthorized.')
        return redirect('dashboard:home')

    pending  = PaymentRecord.objects.filter(payment_status='PENDING').select_related('patient', 'appointment')
    verified = PaymentRecord.objects.filter(payment_status='VERIFIED').select_related('patient', 'appointment').order_by('-verified_at')[:20]
    rejected = PaymentRecord.objects.filter(payment_status='REJECTED').select_related('patient', 'appointment').order_by('-updated_at')[:10]

    return render(request, 'payments/admin_list.html', {
        'pending':  pending,
        'verified': verified,
        'rejected': rejected,
    })


# ══════════════════════════════════════════════════════════════
# Stripe webhook placeholder (for future production)
# ══════════════════════════════════════════════════════════════
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

@csrf_exempt
def stripe_webhook(request):
    """Reserved for future Stripe integration in production"""
    return HttpResponse(status=200)