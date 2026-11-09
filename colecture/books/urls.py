from django.urls import path

from . import views

app_name = 'books'

urlpatterns = [
    path('search/', views.search_books, name='search'),
    path('register/', views.register_book, name='register_book'),
    path('<int:book_id>/', views.book_detail, name='book_detail'),
    path('<int:book_id>/edit/', views.edit_book, name='edit_book'),
    path('<int:book_id>/delete/', views.delete_book, name='delete_book'),
    path("shelf/", views.manage_bookshelf, name='manage_bookshelf'),
    path("shelf/<int:book_id>/mark-read/", views.mark_book_as_read, name='mark_book_as_read'),
    path("shelf/<int:book_id>/progress/", views.save_reading_progress, name='save_reading_progress'),
    path('lookup/', views.books_lookup, name='lookup'),
    path("reading/register/", views.register_reading_session, name="register_reading_session"),
]
