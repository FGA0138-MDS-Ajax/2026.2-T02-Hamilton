from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required

from books.models import Book

def index(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    return render(request, 'main/index.html')

def search(request):
    genres = Book.objects.genres()
    return render(request, 'main/search.html', {'genres': genres})
