from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.db.models import Avg, Count
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django.utils.http import urlencode
from django.views.decorators.http import require_GET

from .forms import BookForm, BookReviewForm
from .models import Book, BookReview

SEARCH_LIMIT = 50


# Registrar um novo livro
@login_required
def register_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)

        if form.is_valid():
            # salva o formulário mas não manda o livro para a db
            book_instance = form.save(commit=False)
            # manualmente preenche o atributo created_by
            book_instance.created_by = request.user
            # salva para a db
            book_instance.save()

            messages.success(request, 'Livro cadastrado com sucesso!')

            return redirect('books:register_book')

    else:
        form = BookForm()

    return render(request, 'books/book_form.html', {'form': form, 'action':'register'})


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

    return render(request, 'books/book_form.html', {'form': form, 'action':'edit'})


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


def _iso_date(value):
    """Converte date/datetime para 'AAAA-MM-DD' (formato lido pelo JS)."""
    if value is None:
        return ""
    if hasattr(value, "date"):  # datetime
        value = value.date()
    return value.isoformat()


# Página de detalhes de um livro + cadastro/edição da avaliação do usuário
def book_detail(request, book_id):
    book = Book.objects.filter(pk=book_id).first()

    if book is None:
        return render(request, "books/book_detail.html",
                      {"id": book_id, "livro": None}, status=404)

    # Avaliação anterior do usuário logado (se existir) para editá-la
    existing_review = None
    if request.user.is_authenticated:
        existing_review = BookReview.objects.filter(
            book=book,
            user=request.user
        ).first()

    if request.method == "POST":
        # Só usuários autenticados podem avaliar
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        form = BookReviewForm(request.POST, instance=existing_review)

        if form.is_valid():
            review = form.save(commit=False)
            review.book = book
            review.user = request.user
            review.save()

            messages.success(request, 'Avaliação salva com sucesso!')

            # Post/Redirect/Get: evita reenvio do formulário ao recarregar
            return redirect(request.path)
    else:
        form = BookReviewForm(instance=existing_review)

    # Média e total calculados no banco
    stats = BookReview.objects.filter(book=book).aggregate(
        media=Avg("rating"),
        total=Count("id"),
    )

    reviews = BookReview.objects.filter(book=book).select_related("user").order_by("-id")

    livro = {
        "id": book.id,
        "titulo": book.title,
        "autor": book.author,
        "genero": book.genre,
        "ano": book.publish_year,
        "paginas": book.pages,
        "capa": book.icon or "",
        "sinopse": getattr(book, "synopsis", "") or "",
        "resenhas": [
            {
                "usuario": r.user.get_username(),
                "nota": float(r.rating),
                "texto": r.review or "",
                # ajuste o nome do campo de data se no model for outro
                "data": _iso_date(getattr(r, "created_at", None)),
            }
            for r in reviews
        ],
        "media": float(stats["media"] or 0),
        "totalAvaliacoes": stats["total"],
    }

    login_url = "{}?{}".format(
        resolve_url(settings.LOGIN_URL),
        urlencode({"next": request.path}),
    )

    return render(request, "books/book_detail.html", {
        "id": book_id,
        "livro": livro,
        "form": form,
        "login_url": login_url,
    })