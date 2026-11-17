from django.urls import path

from . import views

app_name = 'logs'

urlpatterns = [
    path('', views.log_list, name='log_list'),
    path('<int:log_id>/', views.log_detail, name='log_detail'),
    path('<int:log_id>/edit/', views.edit_log, name='edit_log'),
    path('<int:log_id>/delete/', views.delete_log_view, name='delete_log'),
]
