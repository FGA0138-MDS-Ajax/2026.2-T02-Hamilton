from django.urls import path
from . import views

app_name = "books"

urlpatterns = [
    path("register/", views.register_book, name="register_book"),
]
