from django import forms
from .models import Book
import re


class BookForm(forms.ModelForm):
    publish_year = forms.IntegerField(
         label="Ano de publicação",
        required=False, 
        widget=forms.NumberInput(attrs={
            'placeholder':'Ex.: 2025',
            'min': 1,
            'max': 9999
            })
    )

    def clean_isbn(self):
        isbn = self.cleaned_data['isbn']

        isbn = isbn.replace('-', '').replace(' ', '')

        # verifica quantidade de caracteres e se são caracteres válidos

        if len(isbn) not in (10, 13):
            raise forms.ValidationError('O ISBN deve ter 10 ou 13 caracteres.')

        if len(isbn) == 13 and not isbn.isdigit():
            raise forms.ValidationError('O ISBN contém caracteres inválidos.')

        if len(isbn) == 10 and not (isbn[:9].isdigit() and isbn[9] in '0123456789X'):
            raise forms.ValidationError('O ISBN contém caracteres inválidos.')

        # valida o ISB de tamanho 10
        if len(isbn) == 10:
            total = sum(
                (10 - i) * (10 if char == 'X' else int(char))
                for i, char in enumerate(isbn)
            )

            if total % 11 != 0:
                raise forms.ValidationError('ISBN-10 inválido.')

        # valida o ISB de tamanho 13
        if len(isbn) == 13:
            total = 0

            for i in range(12):
                weight = 1 if i % 2 == 0 else 3
                total += int(isbn[i]) * weight

            check_digit = (10 - total % 10) % 10

            if check_digit != int(isbn[12]):
                raise forms.ValidationError('ISBN-13 inválido.')

        return isbn

    class Meta:
        model = Book

        fields = [
            'isbn',
            'title',
            'genre',
            'pages',
            'author',
            'publish_year',
            'publisher',
        ]

        labels = {
            'isbn': 'ISBN',
            'title' : 'Título',
            'genre' : 'Gênero',
            'pages' : 'Número de páginas',
            'author' : 'Autor',
            'publish_year' : 'Ano de publicação',
            'publisher' : 'Editora',
        }
