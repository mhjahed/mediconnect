# dashboard/urls.py  — COMPLETE WITH ADMIN ROUTES

from django.urls import path
from . import views
from . import admin_views
from . import admin_views
app_name = 'dashboard'
# dashboard/urls.py — ADD these routes

urlpatterns = [
    path('',                    views.home_view,            name='home'),
    path('attendance/',         views.attendance_view,      name='attendance'),
    path('attendance/mark/',    views.mark_attendance_view, name='mark_attendance'),

    # Admin Panel
    path('admin/',              admin_views.admin_home,             name='admin_home'),
    path('admin/keys/',         admin_views.manage_keys,            name='admin_keys'),
    path('admin/keys/generate/',admin_views.generate_key,           name='generate_key'),
    path('admin/keys/<int:key_id>/revoke/', admin_views.revoke_key, name='revoke_key'),
    path('admin/notices/',      admin_views.manage_notices,         name='admin_notices'),
    path('admin/notices/post/', admin_views.post_notice,            name='post_notice'),
    path('admin/notices/<int:notice_id>/deactivate/', admin_views.deactivate_notice, name='deactivate_notice'),
    path('admin/doctors/',      admin_views.manage_doctors,         name='admin_doctors'),
    path('admin/patients/',     admin_views.manage_patients,        name='admin_patients'),
    path('admin/payments/',     admin_views.payment_verification,   name='admin_payments'),
    path('admin/payments/<uuid:payment_id>/verify/', admin_views.verify_payment, name='verify_payment'),

    # ── STAFF MANAGEMENT (NEW) ─────────────────────────────
    path('admin/staff/',                 admin_views.manage_staff,        name='admin_staff'),
    path('admin/staff/keys/',            admin_views.manage_staff_keys,   name='admin_staff_keys'),
    path('admin/staff/keys/generate/',   admin_views.generate_staff_key,  name='generate_staff_key'),
    path('admin/staff/keys/<int:key_id>/revoke/', admin_views.revoke_staff_key, name='revoke_staff_key'),

    # ID Cards
    path('admin/id-cards/',                          admin_views.manage_staff_ids,    name='admin_id_cards'),
    path('admin/id-cards/generate/<uuid:user_id>/',  admin_views.generate_id_card,    name='generate_id_card'),
    path('admin/id-cards/<uuid:card_id>/',           admin_views.view_id_card,        name='view_id_card'),
    path('admin/id-cards/<uuid:card_id>/edit/',      admin_views.edit_id_card,        name='edit_id_card'),
    path('admin/barcode-sheet/', admin_views.print_barcode_sheet, name='barcode_sheet'),
]
