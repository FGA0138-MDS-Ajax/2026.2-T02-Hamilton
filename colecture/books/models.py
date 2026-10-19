from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, URLValidator
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from decimal import Decimal

ISBN_MAX_LENGTH = 17
TITLE_MAX_LENGTH = 200
GENRE_MAX_LENGTH = 150
AUTHOR_MAX_LENGTH = 200
PUBLISHER_MAX_LENGTH = 200
ICON_MAX_LENGTH = 500


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
                Q(title__icontains=word) | Q(author__icontains=word) | Q(publisher__icontains=word)
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

    # Endereço (URL http/https) da imagem da capa. Opcional: vazio = sem imagem.
    icon = models.CharField(
        max_length=ICON_MAX_LENGTH,
        blank=True,
        validators=[URLValidator(schemes=['http', 'https'])],
    )

    def __str__(self):
        return self.title

# Valida se a nota utiliza intervalos de 0,5 estrelas
def validate_half_star(value):
    if value * 2 != (value * 2).to_integral_value():
        raise ValidationError(
            "A nota deve aumentar em intervalos de 0,5."
        )

# Armazena as avaliações dos livros
class BookReview(models.Model):
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    # Define as notas disponíveis
    RATING_CHOICES = [
        (Decimal("1.0"), "1 estrela"),
        (Decimal("1.5"), "1,5 estrelas"),
        (Decimal("2.0"), "2 estrelas"),
        (Decimal("2.5"), "2,5 estrelas"),
        (Decimal("3.0"), "3 estrelas"),
        (Decimal("3.5"), "3,5 estrelas"),
        (Decimal("4.0"), "4 estrelas"),
        (Decimal("4.5"), "4,5 estrelas"),
        (Decimal("5.0"), "5 estrelas"),
    ]
    # Armazena a nota da avaliação
    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        choices=RATING_CHOICES,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
            validate_half_star,
        ]
    )
    # Associa a avaliação ao usuário
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="book_reviews"
    )
    # Registra as datas de criação e atualização
    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

     # Armazena a resenha
    review = models.TextField(max_length=300, blank=True)

     #Impede que um usuário tenha mais de uma avaliação para o mesmo livro
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["book", "user"],
                name="unique_user_book_review"
            )
        ]
    # Define como a avaliação será representada em texto
    def __str__(self):
        return f"{self.user} - {self.book}: {self.rating}"