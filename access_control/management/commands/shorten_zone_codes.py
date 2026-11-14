# access_control/management/commands/shorten_zone_codes.py

from django.core.management.base import BaseCommand
from access_control.models import AccessZone
import secrets, string


class Command(BaseCommand):
    help = 'Shortens existing zone access codes to barcode-friendly format'

    def handle(self, *args, **options):
        # Mapping of zone types to short codes
        type_codes = {
            'STORAGE':       'STO',
            'SURGERY':       'SUR',
            'MEDICINE':      'MED',
            'INVENTORY':     'INV',
            'COMMON':        'COM',
            'DOCTOR_ROOM':   'DOC',
            'CAFE':          'CAF',
            'STAFF_COMMON':  'SCO',
            'NURSE_ROOM':    'NUR',
            'LAB':           'LAB',
            'RADIOLOGY':     'RAD',
            'ICU':           'ICU',
            'EMERGENCY':     'EMG',
            'PHARMACY':      'PHR',
            'RECEPTION':     'REC',
            'ADMIN_OFFICE':  'ADM',
            'RECORDS_ROOM':  'REC',
            'CONSULTATION':  'CON',
            'WAITING_AREA':  'WAT',
            'MAINTENANCE':   'MNT',
        }

        for zone in AccessZone.objects.all():
            short = type_codes.get(zone.zone_type, 'GEN')
            # Use floor + room number for uniqueness
            new_code = f"MEDI-{short}-F{zone.floor_number}"
            if zone.room_number:
                # Take last 2 chars of room number
                room_suffix = ''.join(c for c in zone.room_number if c.isalnum())[-2:]
                new_code = f"MEDI-{short}-{room_suffix}"

            # Ensure uniqueness
            counter = 1
            base_code = new_code
            while AccessZone.objects.filter(access_code_text=new_code).exclude(id=zone.id).exists():
                new_code = f"{base_code}{counter}"
                counter += 1

            old_code = zone.access_code_text
            zone.access_code_text = new_code
            zone.save()

            self.stdout.write(self.style.SUCCESS(
                f"✅ {zone.name}: {old_code} → {new_code}"
            ))

        self.stdout.write(self.style.SUCCESS('\n🎉 All zone codes shortened!'))