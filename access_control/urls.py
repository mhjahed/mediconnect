# access_control/urls.py

from django.urls import path
from . import views

app_name = 'access_control'    # ← Required

urlpatterns = [
    path('scanner/',    views.scanner_page,     name='scanner'),
    path('api/scan/',   views.process_scan,     name='process_scan'),
    path('logs/',       views.access_logs_view, name='logs'),
]