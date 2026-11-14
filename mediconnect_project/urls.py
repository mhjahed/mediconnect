# mediconnect_project/urls.py  — ADD this to serve vendor files

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.views.static import serve
import os
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('appointments/', include('appointments.urls')),
    path('payments/', include('payments.urls')),
    path('records/', include('medical_records.urls')),
    path('access/', include('access_control.urls')),
    path('favicon.ico', RedirectView.as_view(url='/static/images/favicon.ico')),
    path('notifications/', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header  = '🏥 MediConnect Administration'
admin.site.site_title   = 'MediConnect Admin Portal'
admin.site.index_title  = 'Welcome to MediConnect Control Panel'