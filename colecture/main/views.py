from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from books.models import Book, BookStatus
from books.services import BookRecommendationService

RECOMMENDATIONS_LIMIT = 10

def index(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    return render(request, 'main/index.html')

def search(request):
    genres = Book.objects.genres()
    return render(request, 'main/search.html', {'genres': genres})


# Livros recomendados para o usuário (seção "Recomendados para você" da pesquisa).
# Só lê o BookRecommendationService; a lista já sai ordenada daqui e o front só exibe.
@require_GET
def recommendations(request):
    if not request.user.is_authenticated:
        return JsonResponse({'results': []})

    recommended = BookRecommendationService.get_recommended_books(request.user)
    if isinstance(recommended, dict):
        recommended = _books_from_genre_scores(request.user, recommended)

    books = list(recommended)[:RECOMMENDATIONS_LIMIT]
    results = [
        {
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'genre': book.genre,
            'icon': book.icon,
            'status': '',
        }
        for book in books
    ]

    return JsonResponse({'results': results})


def _books_from_genre_scores(user, genre_scores):
    # Adaptador provisório: hoje o BookRecommendationService devolve só a
    # pontuação por gênero. Aqui viram livros dos gêneros com pontuação
    # positiva (do maior para o menor), sem os que já estão na estante.
    # Quando o serviço devolver a lista de livros, esta função pode sair.
    ranked_genres = [
        genre
        for genre, score in sorted(genre_scores.items(), key=lambda item: item[1], reverse=True)
        if genre and score > 0
    ]
    if not ranked_genres:
        return []

    shelf_ids = BookStatus.objects.filter(user=user).values_list('book_id', flat=True)
    candidates = Book.objects.filter(genre__in=ranked_genres).exclude(id__in=shelf_ids)

    by_genre = {genre: [] for genre in ranked_genres}
    for book in candidates.order_by('title'):
        by_genre[book.genre].append(book)

    return [book for genre in ranked_genres for book in by_genre[genre]]
