# access_control/management/commands/seed_zones.py

from django.core.management.base import BaseCommand
from access_control.models import AccessZone


class Command(BaseCommand):
    help = 'Seeds default hospital access zones'

    def handle(self, *args, **options):
        zones = [
            ('Storage Room',       'STORAGE',      1, 'S-101', 'MEDICONNECT-STORAGE-ROOM-001',      ['ADMIN', 'DOCTOR', 'NURSE']),
            ('Surgery Room A',     'SURGERY',      2, 'SG-201','MEDICONNECT-SURGERY-ROOM-A-201',     ['DOCTOR', 'NURSE']),
            ('Surgery Room B',     'SURGERY',      2, 'SG-202','MEDICONNECT-SURGERY-ROOM-B-202',     ['DOCTOR', 'NURSE']),
            ('Medicine Room',      'MEDICINE',     1, 'M-102', 'MEDICONNECT-MEDICINE-ROOM-102',      ['DOCTOR', 'NURSE', 'ADMIN']),
            ('Inventory Room',     'INVENTORY',    1, 'I-103', 'MEDICONNECT-INVENTORY-ROOM-103',     ['ADMIN']),
            ('Common Room',        'COMMON',       1, 'C-104', 'MEDICONNECT-COMMON-ROOM-104',        ['ALL']),
            ('Doctor Room 1',      'DOCTOR_ROOM',  3, 'D-301', 'MEDICONNECT-DOCTOR-ROOM-301',        ['DOCTOR']),
            ('Doctor Room 2',      'DOCTOR_ROOM',  3, 'D-302', 'MEDICONNECT-DOCTOR-ROOM-302',        ['DOCTOR']),
            ('Café',               'CAFE',         1, 'CF-105','MEDICONNECT-CAFE-105',                ['ALL']),
            ('Staff Common Room',  'STAFF_COMMON', 2, 'SC-203','MEDICONNECT-STAFF-COMMON-203',       ['DOCTOR', 'NURSE', 'ADMIN']),
            ('Nurse Room',         'NURSE_ROOM',   2, 'N-204', 'MEDICONNECT-NURSE-ROOM-204',         ['NURSE', 'DOCTOR']),
            ('Laboratory',         'LAB',          1, 'L-106', 'MEDICONNECT-LAB-106',                 ['DOCTOR', 'ADMIN']),
            ('Radiology',          'RADIOLOGY',    2, 'R-205', 'MEDICONNECT-RADIOLOGY-205',           ['DOCTOR']),
            ('ICU',                'ICU',          3, 'ICU-303','MEDICONNECT-ICU-303',                ['DOCTOR', 'NURSE']),
            ('Emergency Room',     'EMERGENCY',    1, 'ER-107','MEDICONNECT-EMERGENCY-107',           ['ALL']),
            ('Pharmacy',           'PHARMACY',     1, 'PH-108','MEDICONNECT-PHARMACY-108',            ['DOCTOR', 'NURSE', 'ADMIN']),
            ('Reception',          'RECEPTION',    1, 'RC-109','MEDICONNECT-RECEPTION-109',           ['ALL']),
            ('Admin Office',       'ADMIN_OFFICE', 3, 'A-304', 'MEDICONNECT-ADMIN-OFFICE-304',       ['ADMIN']),
            ('Records Room',       'RECORDS_ROOM', 2, 'RR-206','MEDICONNECT-RECORDS-ROOM-206',       ['ADMIN', 'DOCTOR']),
            ('Consultation Room 1','CONSULTATION', 2, 'CN-207','MEDICONNECT-CONSULTATION-207',       ['DOCTOR']),
            ('Waiting Area',       'WAITING_AREA', 1, 'W-110', 'MEDICONNECT-WAITING-AREA-110',       ['ALL']),
            ('Maintenance Room',   'MAINTENANCE',  0, 'MT-B01','MEDICONNECT-MAINTENANCE-B01',        ['ADMIN']),
        ]

        created = 0
        for name, ztype, floor, room, code, roles in zones:
            _, was_created = AccessZone.objects.get_or_create(
                access_code_text=code,
                defaults={
                    'name':          name,
                    'zone_type':     ztype,
                    'floor_number':  floor,
                    'room_number':   room,
                    'allowed_roles': roles,
                    'is_active':     True,
                }
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'✅ {name} ({code})'))

        self.stdout.write(self.style.SUCCESS(f'\n🏥 {created} zones created. Total: {AccessZone.objects.count()}'))