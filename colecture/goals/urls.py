from django.urls import path

from . import views

app_name = "goals"

urlpatterns = [
    path("create/", views.create_profile_goal, name="create_profile_goal"),
    path("create/community/<int:community_id>/", views.create_community_goal, name="create_community_goal"),
    path("<int:goal_id>/", views.view_goal, name="view_goal"),
    path("<int:goal_id>/edit/", views.edit_goal, name="edit_goal"),
    path("<int:goal_id>/join/", views.join_goal, name="join_goal"),
    path("<int:goal_id>/leave/", views.leave_goal, name="leave_goal"),
    path("reading-sessions/register/",views.register_reading_session,name="register_reading_session"),
]
