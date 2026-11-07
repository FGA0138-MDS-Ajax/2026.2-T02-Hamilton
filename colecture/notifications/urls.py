from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('<int:notification_id>/dismiss/', views.dismiss_notification, name='dismiss_notification'),
    
]