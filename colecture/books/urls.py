from django.urls import path

from . import views

app_name = 'books'

urlpatterns = [
    path('search/', views.search_books, name='search'),
    path('register/', views.register_book, name='register_book'),
    path('<int:book_id>/edit/', views.edit_book, name='edit_book'),
    path('<int:book_id>/delete/', views.delete_book, name='delete_book'),
]
