from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BookForm
from .models import Book

# Create your views here.
# Registrar um novo livro


@login_required
def register_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('books:register_book')

    else:
        form = BookForm()

    return render(request, 'books/book_form.html', {'form': form})


# Editar livros


@login_required
def edit_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if not (request.user.is_superuser or request.user == book.created_by):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)

        if form.is_valid():
            form.save()
            return redirect('books:edit_book', book_id=book.id)

    else:
        form = BookForm(instance=book)

    return render(request, 'books/book_form.html', {'form': form})


# Deletar livro cadastrado
@login_required
def delete_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)

    if not (request.user.is_superuser or request.user == book.created_by):
        return HttpResponseForbidden()

    if request.method == 'POST':
        book.delete()
        return redirect('books:register_book')

    return render(request, 'books/book_form.html', {'book': book})
