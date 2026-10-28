from django import forms
from .models import Book, BookReview

# 1. Defina as opções de gênero aqui em cima
GENRE_CHOICES = [
    ('', 'Selecione o gênero'),
    ('ficcao', 'Ficção Científica'),
    ('romance', 'Romance'),
    ('fantasia', 'Fantasia'),
    ('misterio', 'Mistério / Suspense'),
    ('biografia', 'Biografia'),
    ('historia', 'História'),
    ('autoajuda', 'Desenvolvimento Pessoal'),
    ('didatico', 'Didático / Acadêmico'),
    ('outros', 'Outros'),
]


class BookForm(forms.ModelForm):
    # 2. Insira o campo genre personalizado aqui dentro
    genre = forms.ChoiceField(
        choices=GENRE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select-custom'}),
        label='Gênero'
    )

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

        if len(isbn) not in (10, 13):
            raise forms.ValidationError('O ISBN deve ter 10 ou 13 caracteres.')

        if len(isbn) == 13 and not isbn.isdigit():
            raise forms.ValidationError('O ISBN contém caracteres inválidos.')

        if len(isbn) == 10 and not (isbn[:9].isdigit() and isbn[9] in '0123456789X'):
            raise forms.ValidationError('O ISBN contém caracteres inválidos.')

        if len(isbn) == 10:
            total = sum(
                (10 - i) * (10 if char == 'X' else int(char))
                for i, char in enumerate(isbn)
            )
            if total % 11 != 0:
                raise forms.ValidationError('ISBN-10 inválido.')

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
        # 3. Mantenha todos os campos necessários do seu modelo
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
        labels = {
            "rating": "Nota",
            "review": "Resenha",
        }
        widgets = {
            "rating": forms.Select(),
            "review": forms.Textarea(attrs={
                "maxlength": 300,
                "rows": 4,
                "placeholder": "Escreva sua resenha (opcional)...",
            }),
        }

    def clean_rating(self):
        rating = self.cleaned_data["rating"]
        if rating < 1 or rating > 5:
            raise forms.ValidationError("A nota deve estar entre 1 e 5.")
        if rating % 1 != 0:
            raise forms.ValidationError(
                "Selecione uma nota em intervalos de 1 estrela."
            )
        return rating