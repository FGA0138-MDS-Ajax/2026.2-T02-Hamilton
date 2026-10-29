from django.test import TestCase, Client;
from django.urls import reverse;
from django.contrib.auth import get_user_model;

from .models import Book, BookReview, SYNOPSIS_MAX_LENGTH;
from .forms import BookForm, GENRE_CHOICES;
from .views import SEARCH_LIMIT;

# Create your tests here.
class CT02(TestCase):
    def setUp(self):
        self.client = Client();

    def post_register_book(self, isbn=None, title=None, synopsis=None):
        return self.client.post(
            reverse("books:register_book"),
            {
                'isbn':isbn or '978-8532511010',
                'title':title or 'Book 1',
                'genre':GENRE_CHOICES[1][0],
                'pages':10,
                'author': 'Author 1',
                'synopsis': synopsis or 'Valid synopsis',
                'publisher':'Publisher 1',
            }
        );

    # cria um formulário de livro apenas com os campos obrigatórios para teste
    def create_book_form(self, isbn, title=None, author=None, synopsis=None):
        return BookForm(data={
            'isbn':isbn,
            'title':title or 'New Book',
            'author':author or 'New Author',
            'synopsis':synopsis,
            'genre':GENRE_CHOICES[1][0]
        });

    def create_book(self, isbn=None,title=None, author=None, created_by=None, genre=None):
        return Book.objects.create(
            isbn = isbn or '978-3-16-148410-0',
            title = title or 'New Book',
            author = author or 'New Author',
            created_by = created_by or None,
            genre=genre or GENRE_CHOICES[1][0]
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
        isbn_valido = '978-8532511010';

        user = get_user_model().objects.create_user(username='NewAccount');
        self.client.force_login(user);

        # tenta registrar o livro com informações inválidas.
        response = self.post_register_book(isbn_invalido);
        self.assertNotEqual(response.status_code, 302);
        self.assertFalse(Book.objects.filter(isbn=isbn_invalido).exists());

        # valida se não é possível regitrar um livro com uma sinopse maior que o limite.
        response1 = self.post_register_book(isbn=isbn_valido, synopsis="i"*(SYNOPSIS_MAX_LENGTH+1));
        self.assertNotEqual(response1.status_code, 302);
        self.assertFalse(Book.objects.filter(isbn=isbn_valido).exists());

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
            'genre':GENRE_CHOICES[1][0],
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

    # TESTES DE EXCLUSÃO DE LIVRO
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

    # TESTES DE PESQUISA
    def test_book_search(self):
        """
        Cria dois livros para teste com atributos
        semelhantes e diferentes.
        """
        book1 = self.create_book(
            isbn='9783161484100',
            title='Book 1',
            author='Author 1',
            genre='Magic'
        );
        book2 = self.create_book(
            isbn='9780132350884',
            title='Harry Potter',
            author='J. K. Rowling',
            genre='Magic'
        );

        # url de pesquisa
        search_url = reverse("books:search");

        """
        verifica se a pesquisa pelo título do
        primeiro livro (book 1) retorna apenas
        e corretamente o primeiro livro.
        """
        response0 = self.client.get(
            search_url,
            data={
                'q':book1.title,
            }
        );
        self.assertEqual(response0.status_code, 200);
        response0_results = response0.json().get('results');
        self.assertIsNotNone(response0_results);
        self.assertEqual(response0.json().get('total', -1), 1);
        self.assertTrue(
            response0_results[0].get('isbn')==book1.isbn and 
            response0_results[0].get('title')==book1.title and
            response0_results[0].get('author')==book1.author and
            response0_results[0].get('genre')==book1.genre and
            response0_results[0].get('pages')==book1.pages
        );

        """
        verifica se a pesquisa por um termo
        diferente de todos os livros
        registrados retorna 0 resultados.
        """
        response1 = self.client.get(
            search_url,
            data={
                'q':(book1.title+book2.title)[::-1],
            }
        );
        self.assertEqual(response1.status_code, 200);
        self.assertEqual(response1.json().get('total', -1), 0);

        """
        verifica se a pesquisa por gênero
        retorna todos os livros daquele gênero
        """
        response3 = self.client.get(
            search_url,
            data={
                'genre':book1.genre
            }
        );
        self.assertEqual(response3.status_code, 200);
        self.assertEqual(response3.json().get('total', -1), 2);

    def test_max_search(self):
        for i in range(SEARCH_LIMIT+1):
            # cria um isbn único para cada livro gerado,
            unique_isbn = f"978316148{i:04d}0" 
            
            Book.objects.create(
                isbn=unique_isbn,
                title=f"Test Book {i}",
                author="Test Author",
            );
        
        search_url = reverse("books:search");

        response = self.client.get(
            search_url,
            data={
                'q':'Test Book'
            }
        );
        results = response.json().get('results');

        self.assertEqual(response.status_code, 200);
        self.assertIsNotNone(results);
        self.assertLessEqual(len(results), SEARCH_LIMIT);

    # TESTES DE REVIEW
    def test_review_VALID(self):
        # cria um livro para teste
        user = get_user_model().objects.create_user(username="Account 1");
        book1 = self.create_book();

        self.client.force_login(user);

        url_review = reverse("books:book_detail", kwargs={'book_id':book1.id});

        response = self.client.post(
            url_review,
            data={
                'rating': '1.0',
                'review':'Terrible book!'
            }
        );

        self.assertEqual(response.status_code, 302);
        self.assertTrue(BookReview.objects.filter(user=user).exists());

        newReview = "Actually, nevermind."
        response1 = self.client.post(
            url_review,
            data={
                'rating': '1.0',
                'review':newReview
            }
        );

        self.assertEqual(response1.status_code, 302);
        review = BookReview.objects.get(user=user);
        self.assertEqual(review.review, newReview);
        self.assertEqual(review.rating, 1);
        # valida se o usuário tem apenas 1 review mesmo postando duas.
        self.assertEqual(len(BookReview.objects.filter(user=user)), 1);
    
    def test_review_INVALID(self):
        # cria um livro para teste
        user = get_user_model().objects.create_user(username="Account 1");
        book1 = self.create_book();

        url_review = reverse("books:book_detail", kwargs={'book_id':book1.id});
        url_invalid_review = reverse("books:book_detail", kwargs={'book_id':book1.id+1});

        # tenta avaliar sem fazer login
        response = self.client.post(
            url_review,
            data={
                'rating': '1.0',
                'review':'Terrible book!'
            }
        );
        self.assertRedirects(response, f"{reverse("accounts:login")}?next={url_review}");
        self.assertFalse(BookReview.objects.filter(review='Terrible book!').exists());

        self.client.force_login(user);

        # tenta avaliar com login mas com informações inválidas
        invalid_data = [
            {'rating': 1, 'review':'Terrible book!'},
            {'rating': 'Good book', 'review':3},
            {'rating': '9.0'},
            {
                'rating': '5.0', 'review':"""
Hey, does anybody want coffee? Who wants coffee? I just made a fresh pot of coffee. Does anybody want coffee?
Hey, hey, hey. Who wants coffee? Does anybody want coffee? Who wants coffee?
"""*3},
            {},            
        ]
        for data in invalid_data:
            response0 = self.client.post(
                url_review,
                data=data
            );
            self.assertNotEqual(response0.status_code, 302);

        self.assertNotEqual(
            self.client.post(
                url_invalid_review,
                data={
                    'rating':'1.0',
                    'review':'Terrible book!'
                }
            ),
            302
        );



