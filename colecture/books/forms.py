from django import forms
from .models import Book, BookReview


class BookForm(forms.ModelForm):
    publish_year = forms.IntegerField(
        label="Ano de publicação",
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Ex.: 2025',
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

        # valida o ISBN de tamanho 10
        if len(isbn) == 10:
            total = sum(
                (10 - i) * (10 if char == 'X' else int(char))
                for i, char in enumerate(isbn)
            )

            if total % 11 != 0:
                raise forms.ValidationError('ISBN-10 inválido.')

        # valida o ISBN de tamanho 13
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
            'synopsis',
            'genre',
            'pages',
            'author',
            'publish_year',
            'publisher',
            'icon',
        ]

        labels = {
            'isbn': 'ISBN',
            'title': 'Título',
            'synopsis': 'Sinopse',
            'genre': 'Gênero',
            'pages': 'Número de páginas',
            'author': 'Autor',
            'publish_year': 'Ano de publicação',
            'publisher': 'Editora',
            'icon': 'Ícone (URL da imagem)',
        }

        widgets = {
            'icon': forms.URLInput(attrs={
                'placeholder': 'Ex.: https://site.com/capa.jpg',
            }),
        }


# Cadastrar e editar avaliações de livros
class BookReviewForm(forms.ModelForm):

    class Meta:
        model = BookReview
        fields = ["rating", "review"]

        # Define os nomes dos campos exibidos
        labels = {
            "rating": "Nota",
            "review": "Resenha",
        }

        # Personaliza os campos visuais
        widgets = {
            "rating": forms.Select(),
            "review": forms.Textarea(attrs={
                "maxlength": 300,
                "rows": 4,
                "placeholder": "Escreva sua resenha (opcional)...",
            }),
        }

    # Valida se a nota está entre 1 e 5 e segue intervalos de 1 estrela
    def clean_rating(self):
        rating = self.cleaned_data["rating"]

        if rating < 1 or rating > 5:
            raise forms.ValidationError("A nota deve estar entre 1 e 5.")

        if rating % 1 != 0:
            raise forms.ValidationError(
                "Selecione uma nota em intervalos de 1 estrela."
            )

        return rating