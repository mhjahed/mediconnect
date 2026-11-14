# payments/urls.py — REPLACE WITH THIS

from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # ─── Patient-facing ───────────────────────────────────
    path('checkout/<uuid:appointment_id>/',
         views.checkout_view,
         name='checkout'),

    path('submit/bank/<uuid:appointment_id>/',
         views.submit_bank_transfer,
         name='submit_bank'),

    path('submit/mobile/<uuid:appointment_id>/',
         views.submit_mobile_banking,
         name='submit_mobile'),

    path('submit/other/<uuid:appointment_id>/',
         views.submit_other_payment,
         name='submit_other'),

    path('pending/<uuid:payment_id>/',
         views.payment_pending,
         name='pending'),

    path('success/',
         views.payment_success,
         name='success'),

    path('failed/',
         views.payment_failed,
         name='failed'),

    # ─── Admin-facing ─────────────────────────────────────
    path('admin/list/',
         views.admin_payment_list,
         name='admin_list'),

    path('admin/verify/<uuid:payment_id>/',
         views.verify_payment,                # ⬅ FIXED: was admin_verify_payment
         name='admin_verify'),

    # ─── Future Stripe (placeholder) ──────────────────────
    path('webhook/',
         views.stripe_webhook,
         name='webhook'),
]