from django.urls import path

from . import views

app_name = 'rewards'

urlpatterns = [
    path('insignias/', views.insignias_view, name='insignias'),
]
