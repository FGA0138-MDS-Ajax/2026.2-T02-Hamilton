from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from .forms import BookForm, BookReviewForm
from .models import Book, BookReview
from .forms import BookReviewForm

SEARCH_LIMIT = 50

# Create your views here.
# Registrar um novo livro


@login_required
def register_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)

        if form.is_valid():
            # salva o formulário mas não manda o livro para a db
            book_instance = form.save(commit=False);
            # manualmente preenche o atributo created_by
            book_instance.created_by = request.user;
            # salva para a db
            book_instance.save();

            messages.success(request, 'Livro cadastrado com sucesso!')

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


            messages.success(request, 'Livro editado com sucesso!')


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


        messages.success(request, 'Livro removido com sucesso!')


        return redirect('books:register_book')

    return render(request, 'books/book_form.html', {'book': book})


# Busca de livros no banco (usada pela página main:search)
@require_GET
def search_books(request):
    term = request.GET.get('q', '')
    genre = request.GET.get('genre', '')

    queryset = Book.objects.search(term, genre)
    total = queryset.count()

    results = [
        {
            'id': book.id,
            'isbn': book.isbn,
            'title': book.title,
            'author': book.author,
            'genre': book.genre,
            'pages': book.pages,
            'year': book.publish_year,
            'publisher': book.publisher,
            'icon': book.icon,
        }
        for book in queryset[:SEARCH_LIMIT]
    ]

    return JsonResponse({'total': total, 'results': results})

# Cadastrar ou editar a avaliação de um livro
@login_required
def review_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    #Busca uma avaliação anterior do usuário para esse livro
    existing_review = BookReview.objects.filter(
        book=book,
        user=request.user
    ).first()

    #Verifica se o formulário foi enviado
    if request.method == "POST":
        form = BookReviewForm(
            request.POST,
            instance=existing_review
        )

        #Valida os dados enviados
        if form.is_valid():
            review = form.save(commit=False)
            review.book = book
            review.user = request.user

            #Salva a avaliação no banco de dados
            review.save()

            return redirect(request.path)

    #Exibe o formulário vazio ou preenchido com a avaliação
    else:
        form = BookReviewForm(instance=existing_review)

    return render(request, "books/book_review_STUB.html", {
        "book": book,
        "form": form,
    })