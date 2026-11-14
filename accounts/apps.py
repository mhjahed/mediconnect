# accounts/apps.py
from django.apps import AppConfig
class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = '👤 Accounts & Authentication'

# dashboard/apps.py
from django.apps import AppConfig
class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'
    verbose_name = '📊 Dashboards'

# appointments/apps.py
from django.apps import AppConfig
class AppointmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'appointments'
    verbose_name = '📅 Appointments'

# payments/apps.py
from django.apps import AppConfig
class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'
    verbose_name = '💳 Payments'

# notifications/apps.py
from django.apps import AppConfig
class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
    verbose_name = '🔔 Notifications'

# medical_records/apps.py
from django.apps import AppConfig
class MedicalRecordsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'medical_records'
    verbose_name = '📋 Medical Records'

# access_control/apps.py
from django.apps import AppConfig
class AccessControlConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'access_control'
    verbose_name = '🔐 Access Control'