from django.urls import path;

from . import views;

app_name = "forums"

urlpatterns = [
    path("<int:forum_id>", views.ViewForum.as_view(), name="view_forum"),
    path("messages/<int:message_id>/delete/", views.delete_message, name="delete_message"),
]
