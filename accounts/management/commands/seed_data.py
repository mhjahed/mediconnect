# accounts/management/commands/seed_data.py

import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, time

from accounts.models import (
    CustomUser, DoctorProfile, PatientProfile,
    DoctorAccessKey, DoctorAttendance, AdminNotice
)
from dashboard.models import DoctorSchedule


class Command(BaseCommand):
    help = 'Seeds database with default doctors, patients, and access keys'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('🌱 Seeding MediConnect Database...'))

        # ══════════════════════════════════════════════
        # ADMIN
        # ══════════════════════════════════════════════
        admin, created = CustomUser.objects.get_or_create(
            email='admin@mediconnect.com',
            defaults={
                'username':    'admin',
                'first_name':  'Super',
                'last_name':   'Admin',
                'role':        'ADMIN',
                'is_staff':    True,
                'is_superuser': True,
                'is_verified': True,
            }
        )
        if created:
            admin.set_password('admin12345')
            admin.save()
            self.stdout.write(self.style.SUCCESS('✅ Admin: admin@mediconnect.com / admin12345'))
        else:
            self.stdout.write('   Admin already exists.')

        # ══════════════════════════════════════════════
        # DOCTORS (3 doctors with different specialties)
        # ══════════════════════════════════════════════
        doctors_data = [
            {
                'email':      'dr.rahim@mediconnect.com',
                'username':   'dr.rahim',
                'first_name': 'Abdur',
                'last_name':  'Rahim',
                'phone':      '01711111111',
                'specialty':  'CARDIOLOGY',
                'bio':        'Senior cardiologist with 15 years of experience in interventional cardiology. Specialist in heart failure management and preventive cardiology.',
                'experience': 15,
                'fee':        1500.00,
                'license':    'MD-BD-001',
                'education':  'MBBS, FCPS (Cardiology) — Dhaka Medical College',
                'languages':  'Bengali, English',
                'rating':     4.8,
                'reviews':    124,
                'schedule': [
                    ('MON', '09:00', '17:00', 30),
                    ('TUE', '09:00', '17:00', 30),
                    ('WED', '09:00', '13:00', 30),
                    ('THU', '09:00', '17:00', 30),
                    ('SAT', '10:00', '14:00', 30),
                ],
            },
            {
                'email':      'dr.fatima@mediconnect.com',
                'username':   'dr.fatima',
                'first_name': 'Fatima',
                'last_name':  'Khatun',
                'phone':      '01722222222',
                'specialty':  'NEUROLOGY',
                'bio':        'Neurologist specializing in migraine, epilepsy and stroke management. Trained at BSMMU with fellowship in clinical neuroscience.',
                'experience': 10,
                'fee':        1200.00,
                'license':    'MD-BD-002',
                'education':  'MBBS, MD (Neurology) — BSMMU',
                'languages':  'Bengali, English, Hindi',
                'rating':     4.6,
                'reviews':    87,
                'schedule': [
                    ('MON', '10:00', '16:00', 30),
                    ('WED', '10:00', '16:00', 30),
                    ('THU', '10:00', '16:00', 30),
                    ('FRI', '10:00', '14:00', 30),
                    ('SUN', '11:00', '15:00', 30),
                ],
            },
            {
                'email':      'dr.karim@mediconnect.com',
                'username':   'dr.karim',
                'first_name': 'Mohammad',
                'last_name':  'Karim',
                'phone':      '01733333333',
                'specialty':  'DENTISTRY',
                'bio':        'Expert dental surgeon with specialization in orthodontics and cosmetic dentistry. Uses latest technology for painless procedures.',
                'experience': 8,
                'fee':        800.00,
                'license':    'MD-BD-003',
                'education':  'BDS, MDS (Orthodontics) — UDCH',
                'languages':  'Bengali, English',
                'rating':     4.9,
                'reviews':    156,
                'schedule': [
                    ('MON', '09:00', '15:00', 30),
                    ('TUE', '09:00', '15:00', 30),
                    ('WED', '09:00', '13:00', 30),
                    ('FRI', '09:00', '15:00', 30),
                    ('SAT', '10:00', '14:00', 30),
                ],
            },
        ]

        for doc in doctors_data:
            user, created = CustomUser.objects.get_or_create(
                email=doc['email'],
                defaults={
                    'username':    doc['username'],
                    'first_name':  doc['first_name'],
                    'last_name':   doc['last_name'],
                    'phone_number': doc['phone'],
                    'role':        'DOCTOR',
                    'is_verified': True,
                }
            )

            if created:
                user.set_password('doctor12345')
                user.save()

                # Avoid UNIQUE constraint crash if license_number is already used by another test doctor
                license_num = doc['license']
                if DoctorProfile.objects.filter(license_number=license_num).exists():
                    license_num = f"{license_num}-{str(user.id)[:4]}"

                DoctorProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'specialty':        doc['specialty'],
                        'bio':              doc['bio'],
                        'years_experience': doc['experience'],
                        'consultation_fee': doc['fee'],
                        'license_number':   license_num,
                        'education':        doc['education'],
                        'languages':        doc['languages'],
                        'rating':           doc['rating'],
                        'total_reviews':    doc['reviews'],
                        'is_available':     True,
                    }
                )

                # Mark today's attendance
                DoctorAttendance.objects.get_or_create(
                    doctor=user,
                    date=timezone.now().date(),
                )

                # Create schedule
                for day, start, end, duration in doc['schedule']:
                    DoctorSchedule.objects.get_or_create(
                        doctor=user,
                        day_of_week=day,
                        defaults={
                            'start_time':   time(*[int(x) for x in start.split(':')]),
                            'end_time':     time(*[int(x) for x in end.split(':')]),
                            'slot_duration': duration,
                            'is_available': True,
                        }
                    )

                self.stdout.write(self.style.SUCCESS(
                    f'✅ Doctor: {doc["email"]} / doctor12345 ({doc["specialty"]})'
                ))
            else:
                self.stdout.write(f'   Doctor {doc["email"]} already exists.')

        # ══════════════════════════════════════════════
        # PATIENTS (3 patients)
        # ══════════════════════════════════════════════
        patients_data = [
            {
                'email':      'patient1@gmail.com',
                'username':   'tanvir_ahmed',
                'first_name': 'Tanvir',
                'last_name':  'Ahmed',
                'phone':      '01811111111',
                'gender':     'MALE',
                'dob':        '1995-03-15',
                'blood':      'B+',
                'history':    'Occasional chest pain, family history of heart disease.',
                'allergies':  'Penicillin',
            },
            {
                'email':      'patient2@gmail.com',
                'username':   'nusrat_jahan',
                'first_name': 'Nusrat',
                'last_name':  'Jahan',
                'phone':      '01822222222',
                'gender':     'FEMALE',
                'dob':        '1990-07-22',
                'blood':      'A+',
                'history':    'Chronic migraine, stress-related headaches.',
                'allergies':  'None',
            },
            {
                'email':      'patient3@gmail.com',
                'username':   'rafiq_islam',
                'first_name': 'Rafiq',
                'last_name':  'Islam',
                'phone':      '01833333333',
                'gender':     'MALE',
                'dob':        '1988-11-10',
                'blood':      'O+',
                'history':    'Dental issues, wisdom tooth extraction needed.',
                'allergies':  'Latex',
            },
        ]

        for pat in patients_data:
            user, created = CustomUser.objects.get_or_create(
                email=pat['email'],
                defaults={
                    'username':     pat['username'],
                    'first_name':   pat['first_name'],
                    'last_name':    pat['last_name'],
                    'phone_number': pat['phone'],
                    'gender':       pat['gender'],
                    'date_of_birth': pat['dob'],
                    'role':         'PATIENT',
                    'is_verified':  True,
                }
            )

            if created:
                user.set_password('patient12345')
                user.save()

                PatientProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'blood_type':      pat['blood'],
                        'medical_history': pat['history'],
                        'allergies':       pat['allergies'],
                    }
                )

                self.stdout.write(self.style.SUCCESS(
                    f'✅ Patient: {pat["email"]} / patient12345'
                ))
            else:
                self.stdout.write(f'   Patient {pat["email"]} already exists.')

        # ══════════════════════════════════════════════
        # UNUSED ACCESS KEYS (for testing doctor registration)
        # ══════════════════════════════════════════════
        keys_data = [
            ('CARDIOLOGY', 'For new cardiology hire'),
            ('PEDIATRICS', 'For pediatrics wing expansion'),
            ('PSYCHIATRY', 'For mental health department'),
        ]

        for specialty, notes in keys_data:
            key = DoctorAccessKey.generate_key()
            DoctorAccessKey.objects.create(
                key=key,
                specialty=specialty,
                generated_by=admin,
                notes=notes,
            )
            self.stdout.write(self.style.SUCCESS(
                f'🔑 Access Key: {key} ({specialty})'
            ))

        # ══════════════════════════════════════════════
        # ADMIN NOTICES
        # ══════════════════════════════════════════════
        notices = [
            ('System Maintenance Notice',
             'Server maintenance scheduled for Saturday 2:00 AM - 4:00 AM. Expect brief downtime.',
             'HIGH'),
            ('New Feature: bKash Payment',
             'We now accept bKash, Nagad, and Rocket payments. Bank transfer also available.',
             'NORMAL'),
            ('COVID-19 Protocol Update',
             'All doctors must complete the updated COVID-19 screening protocol before consultations.',
             'CRITICAL'),
        ]

        for title, content, priority in notices:
            AdminNotice.objects.get_or_create(
                title=title,
                defaults={
                    'content':  content,
                    'priority': priority,
                    'posted_by': admin,
                    'is_active': True,
                }
            )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('═' * 55))
        self.stdout.write(self.style.SUCCESS('🎉 DATABASE SEEDED SUCCESSFULLY!'))
        self.stdout.write(self.style.SUCCESS('═' * 55))
        self.stdout.write('')
        self.stdout.write('🔐 LOGIN CREDENTIALS:')
        self.stdout.write(f'   Admin:    admin@mediconnect.com    / admin12345')
        self.stdout.write(f'   Doctor 1: dr.rahim@mediconnect.com / doctor12345 (Cardiology)')
        self.stdout.write(f'   Doctor 2: dr.fatima@mediconnect.com / doctor12345 (Neurology)')
        self.stdout.write(f'   Doctor 3: dr.karim@mediconnect.com / doctor12345 (Dentistry)')
        self.stdout.write(f'   Patient1: patient1@gmail.com / patient12345')
        self.stdout.write(f'   Patient2: patient2@gmail.com / patient12345')
        self.stdout.write(f'   Patient3: patient3@gmail.com / patient12345')
        self.stdout.write('')