from django.test import TestCase, Client;
from django.urls import reverse;
from django.contrib.auth import get_user_model;

from .models import Book;
from .forms import BookForm;

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

    # cria um formulário de livro apenas com os campos obrigatórios para teste
    def create_book_form(self, isbn, title=None, author=None):
        return BookForm(data={
            'isbn':isbn,
            'title':title or 'New Book',
            'author':author or 'New Author'
        });

    def create_book(self, isbn=None,title=None, author=None, created_by=None):
        return Book.objects.create(
            isbn = isbn or '978-3-16-148410-0',
            title = title or 'New Book',
            author = author or 'New Author',
            created_by = created_by or None
        );
    
    # TESTE DE VALIDAÇÃO DO ISBN
    def test_validacao_isbn(self):
        valid = ['978-3-16-148410-0','9783161484100','978-0-13-235088-4','0-321-12521-5','0201633612'];
        invalid = ['978-3-16-148410-9','978316148','97831614841005','978-3-16-ABCDE-0'];

        for isbn in valid:
            form = self.create_book_form(isbn=isbn);
            self.assertTrue(form.is_valid());

        for isbn in invalid:
            form = self.create_book_form(isbn=isbn);
            self.assertFalse(form.is_valid());
        

    # TESTES DE REGISTRO DE LIVRO
    def test_register_book_VALID(self):
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
        self.assertEqual(user, new_book[0].created_by);

    def test_register_book_INVALID(self):
        isbn_invalido = '978';

        user = get_user_model().objects.create_user(username='NewAccount');
        self.client.force_login(user);

        # tenta registrar o livro com informações inválidas.
        response = self.post_register_book(isbn_invalido);
        self.assertNotEqual(response.status_code, 302);
        self.assertFalse(Book.objects.filter(isbn=isbn_invalido).exists());

    def test_register_book_LOGGED_OUT(self):
        user = get_user_model().objects.create_user(username='NewAccount');

        isbn_valido = '978-8532511010';

        url_register_book = reverse('books:register_book');
        url_login = reverse('accounts:login');
        full_redirect = f'{url_login}?next={url_register_book}';

        response = self.post_register_book(isbn_valido);
        self.assertRedirects(response, full_redirect);
        self.assertFalse(Book.objects.filter(isbn=isbn_valido).exists());

    # TESTES DE EDIÇÃO DE LIVRO
    def test_edit_book(self):

        new_data = {
            'isbn' : '978-3-16-148410-0',
            'title' : 'New York',
            'author' : 'Old Author',
        };

        user = get_user_model().objects.create_user(username='New Account');
        author_user = get_user_model().objects.create_user(username='Author User');
        book = self.create_book(created_by=author_user);

        # tenta editar o livro sem login.
        url_edit_book = reverse('books:edit_book', kwargs={'book_id':book.id});
        response0 = self.client.post(
            url_edit_book,
            new_data
        );
        # verifica se o livro não foi alterado
        self.assertRedirects(response0, f'{reverse('accounts:login')}?next={url_edit_book}');
        book.refresh_from_db();
        self.assertNotEqual(book.title, new_data['title']);

        # tenta editar o livro com login de usuário leitor (não autor)
        self.client.force_login(user);
        response1 = self.client.post(
            url_edit_book,
            new_data
        );
        book.refresh_from_db();
        # verifica se o código de status retornado é 403 (proibido)
        self.assertEqual(response1.status_code, 403);
        self.assertNotEqual(book.title, new_data['title']);

        """
        tenta editar o livro com login de usuário autor
        (informações válidas)
        """
        self.client.force_login(author_user);
        response2 = self.client.post(
            url_edit_book,
            new_data
        );
        book.refresh_from_db();
        # verifica se o código de status retornado é 302
        self.assertEqual(response2.status_code, 302);
        self.assertEqual(book.title, new_data['title']);

        """
        tenta editar o livro com login de usuário autor
        (informações inválidas)
        """
        response3 = self.client.post(
            url_edit_book,
            {
                'isbn':'0'
            }
        );
        title_before = book.title;
        book.refresh_from_db();
        self.assertEqual(response3.status_code, 200);
        self.assertEqual(book.title, title_before);

    # TESTES DE EXCLUSÃOM DE LIVRO
    def test_delete_book(self):
        user = get_user_model().objects.create_user(username='New Account');
        author_user = get_user_model().objects.create_user(username='Author User');        

        created_book = self.create_book(created_by=author_user);
        isbn = created_book.isbn;
        url_delete_book = reverse('books:delete_book', kwargs={'book_id':created_book.id});

        # tenta deletar com usuário leitor (não autor)
        self.client.force_login(user);
        response0 = self.client.post(url_delete_book);
        # o site proíbe a ação.
        self.assertEqual(response0.status_code, 403);
        # verifica se o livro ainda existe.
        self.assertTrue(Book.objects.filter(isbn=isbn).exists());

        # tenta deletar com o usuário que registrou o livro
        self.client.force_login(author_user);
        response1 = self.client.post(url_delete_book);
        self.assertRedirects(response1, reverse('books:register_book'));
        self.assertFalse(Book.objects.filter(isbn=isbn).exists());


