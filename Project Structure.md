mediconnect/
│
├── mediconnect_project/          # Main Django project config
│   ├── __init__.py
│   ├── settings.py               # Main settings
│   ├── settings_dev.py           # Development settings
│   ├── urls.py                   # Root URL config
│   ├── wsgi.py
│   └── asgi.py                   # For WebSocket support
│
├── accounts/                     # User management app
│   ├── migrations/
│   ├── templates/
│   │   └── accounts/
│   │       ├── login.html
│   │       ├── register_patient.html
│   │       ├── register_doctor.html
│   │       └── profile.html
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── forms.py
│
├── dashboard/                    # Doctor & Patient dashboards
│   ├── migrations/
│   ├── templates/
│   │   └── dashboard/
│   │       ├── doctor_home.html
│   │       ├── patient_home.html
│   │       ├── attendance.html
│   │       └── admin_panel.html
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   └── urls.py
│
├── appointments/                 # Booking system
│   ├── migrations/
│   ├── templates/
│   │   └── appointments/
│   │       ├── book.html
│   │       ├── search_doctor.html
│   │       ├── doctor_profile.html
│   │       └── confirmation.html
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   └── urls.py
│
├── payments/                     # Stripe payment integration
│   ├── migrations/
│   ├── templates/
│   │   └── payments/
│   │       ├── checkout.html
│   │       ├── success.html
│   │       └── failed.html
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   └── urls.py
│
├── notifications/                # Email automation
│   ├── migrations/
│   ├── management/
│   │   └── commands/
│   │       ├── __init__.py
│   │       └── send_reminders.py
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   └── views.py
│
├── medical_records/              # Prescriptions & Notes
│   ├── migrations/
│   ├── templates/
│   │   └── medical_records/
│   │       ├── history.html
│   │       └── prescription.html
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   └── urls.py
│
├── access_control/               # Barcode/QR Access System
│   ├── migrations/
│   ├── templates/
│   │   └── access_control/
│   │       ├── scanner.html
│   │       ├── access_granted.html
│   │       └── access_denied.html
│   ├── static/
│   │   └── access_control/
│   │       ├── js/
│   │       │   └── barcode_scanner.js
│   │       └── css/
│   │           └── scanner.css
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   └── urls.py
│
├── static/                       # Global static files
│   ├── css/
│   │   ├── main.css
│   │   ├── dashboard.css
│   │   └── components.css
│   ├── js/
│   │   ├── main.js
│   │   ├── charts.js
│   │   └── animations.js
│   └── images/
│       ├── logo.png
│       └── icons/
│
├── media/                        # User uploaded files
│   ├── profile_pics/
│   ├── prescriptions/
│   └── qr_codes/
│
├── templates/                    # Global templates
│   ├── base.html
│   ├── navbar.html
│   ├── footer.html
│   └── 404.html
│
├── .env                          # Environment variables (SECRET)
├── .gitignore
├── manage.py
└── requirements.txt