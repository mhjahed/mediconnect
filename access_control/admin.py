# access_control/admin.py

from django.contrib import admin
from .models import AccessZone, BarcodeAccessLog, PersonalAccessBarcode


@admin.register(AccessZone)
class AccessZoneAdmin(admin.ModelAdmin):
    list_display  = ('name', 'zone_type', 'floor_number', 'room_number', 'access_code_text', 'is_active')
    list_filter   = ('zone_type', 'floor_number', 'is_active')
    search_fields = ('name', 'access_code_text')


@admin.register(BarcodeAccessLog)
class BarcodeAccessLogAdmin(admin.ModelAdmin):
    list_display  = ('timestamp', 'access_result', 'user', 'zone', 'barcode_format', 'scanned_text')
    list_filter   = ('access_result', 'barcode_format', 'timestamp')
    search_fields = ('scanned_text', 'user__email')
    readonly_fields = ('timestamp',)


@admin.register(PersonalAccessBarcode)
class PersonalAccessBarcodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'barcode_text', 'is_active', 'issued_at')
    list_filter  = ('is_active',)