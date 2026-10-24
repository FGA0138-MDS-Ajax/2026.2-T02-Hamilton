from django.urls import path

from . import views

app_name = 'communities'

urlpatterns = [
    path('<int:community_id>', views.view_community, name='view_community'),
]
