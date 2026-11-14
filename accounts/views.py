# accounts/views.py

import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .forms import StaffRegistrationForm
from .forms import PatientRegistrationForm, DoctorRegistrationForm, MediConnectLoginForm
from .models import CustomUser

logger = logging.getLogger('mediconnect')


def home_view(request):
    """Public landing page"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    return render(request, 'accounts/home.html')


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    form = MediConnectLoginForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)

        # Log IP
        ip = request.META.get('REMOTE_ADDR')
        user.last_login_ip = ip
        user.save(update_fields=['last_login_ip'])

        logger.info(f"User logged in: {user.email} ({user.role}) from {ip}")
        messages.success(request, f'Welcome back, {user.get_short_name()}! 👋')
        return redirect('dashboard:home')

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been safely logged out.')
    return redirect('accounts:login')


@require_http_methods(['GET', 'POST'])
def register_patient_view(request):
    """Patient self-registration"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    form = PatientRegistrationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f'Welcome to MediConnect, {user.get_short_name()}! 🎉')
        return redirect('dashboard:home')

    return render(request, 'accounts/register_patient.html', {'form': form})


@require_http_methods(['GET', 'POST'])
def register_doctor_view(request):
    """
    Doctor registration — requires valid Access Key.
    URL is shared privately by Admin only.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    form = DoctorRegistrationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        logger.info(f"New Doctor registered: {user.email}")
        messages.success(request, f'Welcome to MediConnect, Dr. {user.last_name}! 🏥')
        return redirect('dashboard:attendance')

    return render(request, 'accounts/register_doctor.html', {'form': form})


# accounts/context_processors.py
def user_role_context(request):
    """Injects user role info into every template"""
    if request.user.is_authenticated:
        return {
            'is_doctor':  request.user.role == 'DOCTOR',
            'is_patient': request.user.role == 'PATIENT',
            'is_admin':   request.user.role == 'ADMIN' or request.user.is_superuser,
            'user_role':  request.user.role,
        }
    return {}


# accounts/views.py — ADD this view




@require_http_methods(['GET', 'POST'])
def register_staff_view(request):
    """Staff registration — requires valid Access Key"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    form = StaffRegistrationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        logger.info(f"New Staff registered: {user.email}")
        messages.success(request, f'Welcome to MediConnect, {user.get_short_name()}! 🎉')
        return redirect('dashboard:home')

    return render(request, 'accounts/register_staff.html', {'form': form})