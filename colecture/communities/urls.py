from django.urls import path

from . import views

app_name = 'communities'

urlpatterns = [
    path('create/', views.create_community, name='create_community'),
    path('<int:community_id>', views.view_community, name='view_community'),
    path('<int:community_id>/delete/',views.delete_community, name='delete_community'),
    path('<int:community_id>/join', views.JoinCommunityView.as_view(), name='join_community'),
    path('<int:community_id>/leave', views.LeaveCommunityView.as_view(), name='leave_community'),
    path('moderador/', views.moderator_view, name='community_moderator'),
]
