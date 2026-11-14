# appointments/urls.py
# The error: string used instead of importing the actual view function

from django.urls import path
from . import views

# Import the medical_records view directly
from medical_records.views import create_or_edit_record

app_name = 'appointments'

urlpatterns = [
    path('',
         views.appointments_home,
         name='home'),

    path('search/',
         views.search_doctors,
         name='search'),

    path('doctor/<uuid:doctor_id>/',
         views.doctor_profile,
         name='doctor_profile'),

    path('doctor/<uuid:doctor_id>/book/',
         views.book_appointment,
         name='book'),

    path('doctor/<uuid:doctor_id>/slots/',
         views.get_slots_for_date,
         name='slots'),

    path('setup-meet/<uuid:appointment_id>/',
         views.setup_google_meet,
         name='setup_meet'),

    # Doctor writes consultation notes for a paid appointment
    path('record/<uuid:appointment_id>/',
         create_or_edit_record,          # ← actual function, not a string
         name='write_record'),
]
