import json;
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.db.models import Avg, Count
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django.utils.http import urlencode
from django.views.decorators.http import require_GET
from django.db.models import Sum
from decimal import Decimal, ROUND_HALF_UP;
from django.views.decorators.http import require_GET, require_POST

from accounts.models import Profile
from .forms import BookForm, BookReviewForm, ReadingSessionForm
from .models import Book, BookReview, BookStatus, ReadingSession

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

            # MODIFICAÇÃO AQUI: Redireciona de volta para a página de detalhes do livro
            return redirect('books:book_detail', book_id=book.id)

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
    books = list(queryset[:SEARCH_LIMIT])

    # Status de cada livro na estante do usuário logado (vazio se não estiver na estante)
    statuses = {}
    if request.user.is_authenticated:
        statuses = dict(
            BookStatus.objects.filter(
                user=request.user,
                book__in=books
            ).values_list('book_id', 'status')
        )

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
            'status': statuses.get(book.id, ''),
        }
        for book in books
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

@login_required
def manage_bookshelf(request):

    user = request.user;

    if request.method == "POST":
        body = json.loads(request.body);
        book_id = body.get('book_id');
        status = body.get('status');

        # caso o status esteja vazio,
        # deletar o BookStatus correspondente.
        if not status:
            book_status = BookStatus.objects.filter(
                user=user,
                book_id = book_id
            ).first();

            if book_status:
                book_status.delete();
        else:
            if not BookStatus.validate_status(status):
                return HttpResponseForbidden("Invalid status");
        
            BookStatus.objects.update_or_create(
                user=user,
                book=Book.objects.get(id=book_id),
                defaults={
                    'status':status
                }
            );

        return JsonResponse({'success':True});

    statuses = user.book_statuses.all();

    return JsonResponse(
        data={
            status.book.id:status.status
            for status in statuses
        }
    );
    

# Marca um livro da estante como lido com um clique (sem formulário):
# status = Lido, data de conclusão = hoje e progresso = 100%.
@login_required
@require_POST
def mark_book_as_read(request, book_id):
    book_status = BookStatus.objects.filter(
        user=request.user,
        book_id=book_id
    ).select_related('book').first()

    if book_status is None:
        return JsonResponse(
            {'success': False, 'error': 'Livro não encontrado na sua estante.'},
            status=404
        )

    if book_status.status != BookStatus.Status.READ:
        book_status.mark_as_read()

    return JsonResponse({
        'success': True,
        'book_id': book_status.book_id,
        'status': book_status.status,
        'status_label': book_status.get_status_display(),
        'finished_at': _iso_date(book_status.finished_at),
        'progress': book_status.progress_percent,
        'pages': book_status.book.pages,
    })


# Salva o progresso (0-100%) registrado na tela "Registrar leitura",
# para a estante do perfil mostrar a barra de progresso atualizada.
@login_required
@require_POST
def save_reading_progress(request, book_id):
    try:
        percent = Decimal(str(json.loads(request.body or '{}').get('percent')))
    except (ValueError, TypeError, ArithmeticError):
        percent = None

    if percent is None or not percent.is_finite() or not (0 <= percent <= 100):
        return JsonResponse(
            {'success': False, 'error': 'Progresso inválido (use de 0 a 100%).'},
            status=400
        )

    book_status = BookStatus.objects.filter(
        user=request.user,
        book_id=book_id
    ).select_related('book').first()

    if book_status is None:
        return JsonResponse(
            {'success': False, 'error': 'Livro não encontrado na sua estante.'},
            status=404
        )

    book_status.reading_progress = (percent / 100).quantize(
        Decimal('0.001'), rounding=ROUND_HALF_UP
    )
    fields = ['reading_progress']
    if book_status.status == BookStatus.Status.WANT_TO_READ:
        book_status.status = BookStatus.Status.READING
        fields.append('status')
    book_status.save(update_fields=fields)

    return JsonResponse({
        'success': True,
        'book_id': book_status.book_id,
        'status': book_status.status,
        'progress': book_status.progress_percent,
        'pages_read': book_status.pages_read,
    })


LOOKUP_LIMIT = 100
 
 
# Dados dos livros que o usuário marcou como "Lendo" (o status fica no localStorage,
# então o JS manda os ids e recebe título, autor, páginas e capa).
@require_GET
def books_lookup(request):
    ids = [
        int(i) for i in request.GET.get('ids', '').split(',')
        if i.strip().isdigit()
    ][:LOOKUP_LIMIT]
 
    books = Book.objects.filter(pk__in=ids).order_by('title')
 
    results = [
        {
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'genre': book.genre,
            'pages': book.pages,
            'icon': book.icon,
        }
        for book in books
    ]
 
    return JsonResponse({'results': results})
 
 
# Tela "Registrar leitura" aberta ao clicar num livro da estante do perfil (?book=<id>).
@login_required
def reading_session(request):
    return render(request, "books/reading_session.html")


@login_required
def register_reading_session(request):
    if request.method == "POST":
        form = ReadingSessionForm(request.POST, user=request.user)

        if form.is_valid():
            book = form.cleaned_data["book"]
            current_page = form.cleaned_data.get("current_page")
            current_percentage = form.cleaned_data.get("current_percentage")

            if not book.pages:
                form.add_error(
                    "book",
                    "O livro precisa ter a quantidade de páginas informada."
                )

            else:
                with transaction.atomic():

                    #busca ou cria o status do livro
                    book_status, created = BookStatus.objects.get_or_create(
                        user=request.user,
                        book=book,
                    )

                    #busca a quantidade de páginas já lidas
                    previous_page = (
                        ReadingSession.objects.filter(
                            user=request.user,
                            book=book
                        ).aggregate(total=Sum("pages_read"))["total"] or 0
                    )

                    #Converte o percentual informado para página atual
                    if current_percentage is not None:
                        current_page = int(
                            (
                                current_percentage * book.pages
                                / Decimal("100")
                            ).quantize(
                                Decimal("1"),
                                rounding=ROUND_HALF_UP
                            )
                        )

                    #valida se houve avanço na leitura
                    if current_page <= previous_page:
                        field = (
                            "current_page"
                            if form.cleaned_data.get("current_page") is not None
                            else "current_percentage"
                        )

                        form.add_error(
                            field,
                            "O progresso informado deve ser maior que o anterior."
                        )

                    else:
                        #calcula as páginas lidas nesta sessão
                        pages_read = current_page - previous_page

                        reading_session = form.save(commit=False)
                        reading_session.pages_read = pages_read
                        reading_session.user = request.user
                        reading_session.full_clean()
                        reading_session.save()

                        #sessão e ofensiva são salvas juntas (mesma transação)
                        profile, _ = Profile.objects.get_or_create(user=request.user)
                        if profile.register_reading_day(reading_session.date):
                            profile.save(update_fields=["streak", "last_read_date"])

                        #atualiza o percentual total do livro
                        book_status.reading_progress = (
                            Decimal(current_page) / Decimal(book.pages)
                        ).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

                        if current_page >= book.pages:
                            book_status.status = BookStatus.Status.READ
                        else:
                            book_status.status = BookStatus.Status.READING

                        book_status.save(update_fields=["reading_progress", "status"])

                        return redirect("books:register_reading_session")

    else:
        form = ReadingSessionForm(user=request.user)

    return render(
        request,
        "books/register_reading_session.html",
        {"form": form}
    )
