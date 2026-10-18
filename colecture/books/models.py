from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

ISBN_MAX_LENGTH = 17
TITLE_MAX_LENGTH = 200
GENRE_MAX_LENGTH = 150
AUTHOR_MAX_LENGTH = 200
PUBLISHER_MAX_LENGTH = 200


class BookQuerySet(models.QuerySet):
    """Consultas reutilizáveis do catálogo (regras de busca ficam no model."""

    def search(self, term='', genre=''):
        """Filtra por título/autor e, opcionalmente, por gênero.

        Cada palavra do termo precisa aparecer no título OU no autor
        (ex.: "rowling harry" encontra "Harry Potter" de J. K. Rowling).
        """
        queryset = self

        for word in (term or '').split():
            queryset = queryset.filter(
                Q(title__icontains=word) | Q(author__icontains=word)
            )

        genre = (genre or '').strip()
        if genre:
            queryset = queryset.filter(genre__iexact=genre)

        return queryset.order_by('title')

    def genres(self):
        """Gêneros distintos já cadastrados (alimenta o filtro da busca)."""
        return (
            self.exclude(genre='')
            .order_by('genre')
            .values_list('genre', flat=True)
            .distinct()
        )


class Book(models.Model):
    objects = BookQuerySet.as_manager()

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='books',
    )

    isbn = models.CharField(max_length=ISBN_MAX_LENGTH, unique=True, blank=False)
    title = models.CharField(max_length=TITLE_MAX_LENGTH, blank=False)
    genre = models.CharField(max_length=GENRE_MAX_LENGTH, blank=True)
    pages = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], blank=True, null=True
    )
    author = models.CharField(max_length=AUTHOR_MAX_LENGTH, blank=False)
    publish_year = models.PositiveSmallIntegerField(blank=True, null=True)
    publisher = models.CharField(max_length=PUBLISHER_MAX_LENGTH, blank=True)

    def __str__(self):
        return self.title
