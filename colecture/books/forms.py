from django import forms
from .models import Book, BookReview, ReadingSession

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
        required=False,
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # obrigatório no formulário: as metas de páginas usam esse número
        # como limite. No banco continua opcional para não quebrar livros
        # antigos cadastrados sem páginas.
        self.fields['pages'].required = True
        self.fields['pages'].widget.attrs.setdefault('min', 1)

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

class ReadingSessionForm(forms.ModelForm):
    current_page = forms.IntegerField(
        label="Página atual",
        required=False,
        min_value=1
    )

    current_percentage = forms.DecimalField(
        label="Percentual total lido",
        required=False,
        min_value=0,
        max_value=100,
        decimal_places=2,
        max_digits=5
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is not None:
            self.instance.user = user

    class Meta:
        model = ReadingSession
        fields = ["book", "minute_count", "date"]

    def clean(self):
        cleaned = super().clean()

        current_page = cleaned.get("current_page")
        current_percentage = cleaned.get("current_percentage")
        book = cleaned.get("book")

        #exige que o usuário escolha apenas uma forma de informar
        if current_page is None and current_percentage is None:
            raise forms.ValidationError(
                "Informe a página atual ou o percentual total lido."
            )

        if current_page is not None and current_percentage is not None:
            raise forms.ValidationError(
                "Informe somente a página atual ou o percentual."
            )

        #verifica se a página atual é válida
        if current_page is not None and book:
            if book.pages is None:
                self.add_error(
                    "book",
                    "O livro precisa ter a quantidade de páginas informada."
                )
            elif current_page > book.pages:
                self.add_error(
                    "current_page",
                    "A página atual não pode ultrapassar o total de páginas do livro."
                )

        return cleaned