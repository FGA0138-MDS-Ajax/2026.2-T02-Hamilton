from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('history/', views.notification_history, name='history'),
    path('mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('<int:notification_id>/hide/', views.hide_notification_from_popup, name='hide_notification'),
    path('<int:notification_id>/dismiss/', views.dismiss_notification, name='dismiss_notification'),
]