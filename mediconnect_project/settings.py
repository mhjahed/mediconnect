# mediconnect_project/settings.py — COMPLETE CLEAN FILE

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-CHANGE-IN-PRODUCTION')
DEBUG      = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*'] if DEBUG else [
    h.strip() for h in os.getenv('ALLOWED_HOSTS', '.onrender.com').split(',') if h.strip()
]
RENDER_EXTERNAL_HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'https://localhost:8443',
    'http://192.168.0.105:8000',
    'https://192.168.0.105:8443',
    'https://192.168.0.105:8000',
    'https://*.onrender.com',
]

# CSRF Cookie settings — DEFINED ONLY ONCE
CSRF_COOKIE_NAME       = 'csrftoken'
CSRF_COOKIE_HTTPONLY   = False           # ⚠️ MUST be False so JavaScript can read it!
CSRF_USE_SESSIONS      = False
CSRF_COOKIE_SAMESITE   = 'Lax'
CSRF_COOKIE_SECURE     = False           # False for local dev (HTTP allowed)

# ════════════════════════════════════════════════════════════
# SESSION — DEFINED ONLY ONCE (no conflicts)
# ════════════════════════════════════════════════════════════
SESSION_COOKIE_AGE          = 86400          # 24 hours
SESSION_COOKIE_HTTPONLY     = True
SESSION_COOKIE_SAMESITE     = 'Lax'
SESSION_COOKIE_SECURE       = False
SESSION_SAVE_EVERY_REQUEST  = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ════════════════════════════════════════════════════════════
# CORS — Allow scanner to work from any local IP
# ════════════════════════════════════════════════════════════
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'https://localhost:8443',
    'http://192.168.0.105:8000',
    'https://192.168.0.105:8443',
]

# ════════════════════════════════════════════════════════════
# SECURITY HEADERS
# ════════════════════════════════════════════════════════════
SECURE_SSL_REDIRECT     = False                              # Don't force HTTPS in dev
SECURE_REFERRER_POLICY  = 'no-referrer-when-downgrade'
SECURE_HSTS_SECONDS     = 0                                  # Disable HSTS in dev
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD     = False
X_FRAME_OPTIONS         = 'SAMEORIGIN'

# Production-only security
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER       = True
    SECURE_CONTENT_TYPE_NOSNIFF     = True
    SECURE_HSTS_SECONDS             = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS  = True
    SECURE_HSTS_PRELOAD             = True
    SESSION_COOKIE_SECURE           = True
    CSRF_COOKIE_SECURE              = True
    SECURE_SSL_REDIRECT             = True
    SECURE_PROXY_SSL_HEADER         = ('HTTP_X_FORWARDED_PROTO', 'https')

# ════════════════════════════════════════════════════════════
# AUTO-CREATE REQUIRED DIRECTORIES
# ════════════════════════════════════════════════════════════
LOGS_DIR  = BASE_DIR / 'logs'
MEDIA_DIR = BASE_DIR / 'media'

for _dir in [
    LOGS_DIR,
    MEDIA_DIR / 'profile_pics',
    MEDIA_DIR / 'prescriptions',
    MEDIA_DIR / 'qr_codes',
]:
    _dir.mkdir(parents=True, exist_ok=True)

# ════════════════════════════════════════════════════════════
# APPLICATIONS
# ════════════════════════════════════════════════════════════
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'django_extensions',
    'crispy_forms',
    'crispy_bootstrap5',
    'rest_framework',
    'corsheaders',

    # Local apps
    'accounts.apps.AccountsConfig',
    'dashboard.apps.DashboardConfig',
    'appointments.apps.AppointmentsConfig',
    'payments.apps.PaymentsConfig',
    'notifications.apps.NotificationsConfig',
    'medical_records.apps.MedicalRecordsConfig',
    'access_control.apps.AccessControlConfig',
]

# ════════════════════════════════════════════════════════════
# MIDDLEWARE — Order matters!
# ════════════════════════════════════════════════════════════
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',                         # CORS before CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.DoctorAttendanceMiddleware',
]

ROOT_URLCONF = 'mediconnect_project.urls'

# ════════════════════════════════════════════════════════════
# TEMPLATES
# ════════════════════════════════════════════════════════════
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.user_role_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'mediconnect_project.wsgi.application'
ASGI_APPLICATION = 'mediconnect_project.asgi.application'

# ════════════════════════════════════════════════════════════
# DATABASE
# ════════════════════════════════════════════════════════════
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
        }
    }
}

# ════════════════════════════════════════════════════════════
# CUSTOM USER MODEL
# ════════════════════════════════════════════════════════════
AUTH_USER_MODEL = 'accounts.CustomUser'

LOGIN_URL           = '/accounts/login/'
LOGIN_REDIRECT_URL  = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ════════════════════════════════════════════════════════════
# PASSWORD VALIDATION
# ════════════════════════════════════════════════════════════
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ════════════════════════════════════════════════════════════
# STATIC & MEDIA FILES
# ════════════════════════════════════════════════════════════
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

_static_dir = BASE_DIR / 'static'
_static_dir.mkdir(parents=True, exist_ok=True)
STATICFILES_DIRS = [_static_dir]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ════════════════════════════════════════════════════════════
# EMAIL
# ════════════════════════════════════════════════════════════
EMAIL_BACKEND       = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST          = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT          = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS       = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER     = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL  = os.getenv('DEFAULT_FROM_EMAIL', 'MediConnect <noreply@mediconnect.com>')

# ════════════════════════════════════════════════════════════
# STRIPE (Reserved for Future)
# ════════════════════════════════════════════════════════════
STRIPE_PUBLIC_KEY     = os.getenv('STRIPE_PUBLIC_KEY', '')
STRIPE_SECRET_KEY     = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

# ════════════════════════════════════════════════════════════
# SITE CONFIG
# ════════════════════════════════════════════════════════════
SITE_URL          = os.getenv('SITE_URL', 'http://127.0.0.1:8000')
ACCESS_KEY_PREFIX = os.getenv('ACCESS_KEY_PREFIX', 'MEDI')

# ════════════════════════════════════════════════════════════
# CRISPY FORMS
# ════════════════════════════════════════════════════════════
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK          = 'bootstrap5'

# ════════════════════════════════════════════════════════════
# REST FRAMEWORK
# ════════════════════════════════════════════════════════════
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# ════════════════════════════════════════════════════════════
# INTERNATIONALIZATION
# ════════════════════════════════════════════════════════════
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_TZ        = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ════════════════════════════════════════════════════════════
# LOGGING
# ════════════════════════════════════════════════════════════
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': str(LOGS_DIR / 'mediconnect.log'),
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'mediconnect': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}