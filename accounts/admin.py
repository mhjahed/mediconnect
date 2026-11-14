# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, DoctorProfile, PatientProfile, DoctorAccessKey, DoctorAttendance, AdminNotice


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display  = ('email', 'get_full_name', 'role', 'is_active', 'is_verified', 'date_joined')
    list_filter   = ('role', 'is_active', 'is_verified')
    search_fields = ('email', 'first_name', 'last_name')
    ordering      = ('-date_joined',)
    fieldsets      = (
        (None, {'fields': ('email', 'password')}),
        ('Personal', {'fields': ('first_name', 'last_name', 'username', 'phone_number', 'gender', 'date_of_birth', 'profile_picture')}),
        ('Role', {'fields': ('role', 'is_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2', 'role')}),
    )


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialty', 'consultation_fee', 'rating', 'is_available')


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'blood_type')


@admin.register(DoctorAccessKey)
class DoctorAccessKeyAdmin(admin.ModelAdmin):
    list_display  = ('key', 'specialty', 'status', 'generated_by', 'created_at')
    list_filter   = ('status', 'specialty')
    readonly_fields = ('key', 'created_at', 'used_at')

    def save_model(self, request, obj, form, change):
        if not obj.key:
            obj.key = DoctorAccessKey.generate_key()
        if not obj.generated_by:
            obj.generated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DoctorAttendance)
class DoctorAttendanceAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'date', 'time_in', 'status')
    list_filter  = ('date', 'status')


@admin.register(AdminNotice)
class AdminNoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'is_active', 'created_at')
    list_filter  = ('priority', 'is_active')




from .models import StaffProfile, StaffAccessKey

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'designation', 'employee_id', 'shift', 'is_active_employee')
    list_filter  = ('department', 'designation', 'shift', 'employment_type', 'is_active_employee')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'employee_id')


@admin.register(StaffAccessKey)
class StaffAccessKeyAdmin(admin.ModelAdmin):
    list_display = ('key', 'role', 'department', 'designation', 'status', 'created_at')
    list_filter  = ('status', 'role', 'department')
    readonly_fields = ('key', 'created_at', 'used_at')

    def save_model(self, request, obj, form, change):
        if not obj.key:
            obj.key = StaffAccessKey.generate_key()
        if not obj.generated_by:
            obj.generated_by = request.user
        super().save_model(request, obj, form, change)