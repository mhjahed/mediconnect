# accounts/middleware.py — REPLACE entire file

from django.shortcuts import redirect
from django.urls import reverse
from .models import DoctorAttendance


class DoctorAttendanceMiddleware:
    """
    Intercepts every request from staff users (Doctor, Nurse, Staff).
    If they haven't marked attendance today → redirect to Attendance page.
    """

    # Paths that bypass attendance check
    WHITELIST = [
        '/accounts/login/',
        '/accounts/logout/',
        '/accounts/register/',
        '/dashboard/attendance/',           # Allows GET attendance page
        '/dashboard/attendance/mark/',       # ⬅ CRITICAL: Allow POST to mark
        '/admin/',
        '/static/',
        '/media/',
        '/access/',
        '/notifications/api/',
    ]

    # Roles that MUST mark attendance daily
    ATTENDANCE_REQUIRED_ROLES = ['DOCTOR', 'NURSE', 'STAFF']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user

        if (
            user.is_authenticated
            and hasattr(user, 'role')
            and user.role in self.ATTENDANCE_REQUIRED_ROLES
            and not any(request.path.startswith(p) for p in self.WHITELIST)
            and not DoctorAttendance.has_marked_today(user)
        ):
            return redirect(reverse('dashboard:attendance'))

        return self.get_response(request)