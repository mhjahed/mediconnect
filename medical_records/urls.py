# medical_records/urls.py

from django.urls import path
from . import views

app_name = 'medical_records'

urlpatterns = [
    path('',
         views.records_home,
         name='home'),

    path('<uuid:record_id>/',
         views.record_detail,
         name='record_detail'),

    path('create/<uuid:appointment_id>/',
         views.create_or_edit_record,
         name='create'),

    path('edit/<uuid:appointment_id>/',
         views.create_or_edit_record,
         name='edit'),

    path('print/<uuid:record_id>/',
         views.print_prescription,
         name='print'),
]