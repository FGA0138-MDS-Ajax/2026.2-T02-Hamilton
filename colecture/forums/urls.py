from django.urls import path;

from . import views;

app_name = "forums"

urlpatterns = [
    path("<int:forum_id>", views.ViewForum.as_view(), name="view_forum"),
]