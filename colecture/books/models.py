from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

ISBN_MAX_LENGTH = 17
TITLE_MAX_LENGTH = 200
GENRE_MAX_LENGTH = 150
AUTHOR_MAX_LENGTH = 200
PUBLISHER_MAX_LENGTH = 200


class Book(models.Model):
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
