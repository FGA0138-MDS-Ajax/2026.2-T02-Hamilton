from django.test import TestCase, Client;
from django.urls import reverse;
from django.contrib.auth import get_user_model;
from .models import Book;

# Create your tests here.
class CT02(TestCase):
    def setUp(self):
        self.client = Client();

    def post_register_book(self, isbn=None, title=None):
        return self.client.post(
            reverse("books:register_book"),
            {
                'isbn':isbn or '978-8532511010',
                'title':title or 'Book 1',
                'genre':'Genre 1',
                'pages':10,
                'author': 'Author 1',
                'publisher':'Publisher 1',
            }
        );

    # TESTES DE REGISTRO DE LIVRO
    def test_registrar_livro_VALIDO(self):
        isbn = '978-8532511010';

        # versão sem o traço para a pesquisa
        lookup_isbn = isbn.replace('-', '');

        user = get_user_model().objects.create_user(username='NewAccount');

        self.client.force_login(user);

        # certifica que o livro não existia antes.
        existed_before = Book.objects.filter(isbn=lookup_isbn);
        self.assertFalse(existed_before.exists());

        # tenta registrar o livro.
        response = self.post_register_book();

        # verifica se o usuário foi redirecionado (informações válidas)
        self.assertEqual(response.status_code, 302);

        # verifica se o livro foi devidamente registrado na base de dados.
        new_book = Book.objects.filter(isbn=lookup_isbn);
        self.assertTrue(new_book.exists());

    def test_registrar_livro_INVALIDO(self):
        isbn_invalido = '978';

        user = get_user_model().objects.create_user(username='NewAccount');
        self.client.force_login(user);

        # tenta registrar o livro com informações inválidas.
        response = self.post_register_book(isbn_invalido);
        self.assertNotEqual(response.status_code, 302);
        self.assertFalse(Book.objects.filter(isbn=isbn_invalido).exists());

    def test_registrar_livro_DESLOGADO(self):
        user = get_user_model().objects.create_user(username='NewAccount');

        isbn_valido = '978-8532511010';

        url_register_book = reverse('books:register_book');
        url_login = reverse('accounts:login');
        full_redirect = f'{url_login}?next={url_register_book}';

        response = self.post_register_book(isbn_valido);
        self.assertRedirects(response, full_redirect);
        self.assertFalse(Book.objects.filter(isbn=isbn_valido).exists());


