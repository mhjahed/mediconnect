# accounts/urls.py

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('',                    views.home_view,            name='home'),
    path('accounts/login/',     views.login_view,           name='login'),
    path('accounts/logout/',    views.logout_view,          name='logout'),
    path('accounts/register/',  views.register_patient_view,name='register_patient'),
    path('accounts/register/doctor/', views.register_doctor_view, name='register_doctor'),
    path('accounts/register/staff/',      views.register_staff_view,   name='register_staff'),   # ← NEW
]