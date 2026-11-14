# notifications/urls.py

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('',                            views.notification_center,    name='center'),
    path('open/<uuid:notif_id>/',       views.open_notification,      name='open'),

    # API endpoints (bell dropdown)
    path('api/list/',                   views.api_notifications,      name='api_list'),
    path('api/<uuid:notif_id>/read/',   views.api_mark_read,          name='api_read'),
    path('api/<uuid:notif_id>/delete/', views.api_delete_notification, name='api_delete'),
    path('api/mark-all-read/',          views.api_mark_all_read,      name='api_mark_all'),
]