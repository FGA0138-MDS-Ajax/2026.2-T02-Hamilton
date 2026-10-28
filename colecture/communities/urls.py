from django.urls import path

from . import views

app_name = 'communities'

urlpatterns = [
    path('', views.home_community, name='home_community'),
    path('create/', views.create_community, name='create_community'),
    path('<int:community_id>', views.view_community, name='view_community'),
    path('<int:community_id>/delete/',views.delete_community, name='delete_community'),
    path('<int:community_id>/join', views.JoinCommunityView.as_view(), name='join_community'),
    path('<int:community_id>/leave', views.LeaveCommunityView.as_view(), name='leave_community'),
    path('moderator/', views.moderator_view, name='community_moderator'),
    path("<int:community_id>/edit/",views.edit_community,name="edit_community",),
    path('<int:community_id>/members/<int:membership_id>/role/',views.edit_member_role,
        name='edit_member_role',
    ),
    path('<int:community_id>/members/<int:membership_id>/request/',views.manage_membership_request,
        name='manage_membership_request',
    ),
    path('<int:community_id>/members/<int:membership_id>/ban/',views.manage_member_ban,
        name='manage_member_ban',
    ),
]
