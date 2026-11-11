import json;
import importlib
from unittest import mock

from datetime import timedelta, date
from django.test import TestCase, Client;
from django.urls import reverse;
from django.contrib.auth import get_user_model;
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.services import AccountService;
from accounts.models import Profile;
from .models import Book, BookReview, BookStatus, ReadingSession, SYNOPSIS_MAX_LENGTH;
from .forms import BookForm, GENRE_CHOICES;
from .views import SEARCH_LIMIT;
from .forms import ReadingSessionForm
from decimal import Decimal
from django.apps import apps as django_apps
from goals.models import Goal, GoalParticipation;
from goals.services import GoalService;

User = get_user_model()

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
            'genre':GENRE_CHOICES[1][0],
            'pages':10,
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
    def test_numero_de_paginas_obrigatorio(self):
        form = self.create_book_form(isbn='978-8532511010')
        form.data = {**form.data, 'pages': ''}
        self.assertFalse(form.is_valid())
        self.assertIn('pages', form.errors)

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
            'pages' : 10,
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

class CT02_BookStatus(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client();
        cls.author_user = AccountService.create_account(
            get_user_model().objects.create(
                username='Author'
            )
        );
        cls.user1 = AccountService.create_account(
            get_user_model().objects.create(
                username='User1'
            )
        );
        cls.book = Book.objects.create(
            created_by=cls.author_user,
            author=cls.author_user,
            isbn='978-3-16-148410-0',
            title='NewBook',
        );

    def manage_bookshelf(self, status=None, book=None):
        return self.client.post(
            reverse('books:manage_bookshelf'),
            data=json.dumps({
                'book_id':(book and book.id) or self.book.id,
                'status':status
            }),
            content_type="application/json"
        );

    def test_set_statuses(self):
        self.client.force_login(self.author_user);
        status_choices = [
            BookStatus.Status.WANT_TO_READ,
            BookStatus.Status.READING,
            BookStatus.Status.READ,
        ];

        for choice in status_choices:
            response = self.manage_bookshelf(choice);
            self.assertEqual(response.status_code, 200);
            self.assertTrue(
                BookStatus.objects.filter(
                    user=self.author_user,
                    book=self.book,
                    status=choice
                ).exists()
            );

        # valida se o BookStatus é apagado
        # caso nenhum status for enviado
        response1 = self.manage_bookshelf();
        self.assertEqual(response1.status_code, 200);
        self.assertFalse(
            BookStatus.objects.filter(
                user=self.author_user,
                book=self.book,
                status=choice
            ).exists()
        );

    def test_coexistent_diff_statuses(self):
        self.client.force_login(
            self.author_user
        );
        response0 = self.manage_bookshelf(
            BookStatus.Status.READ
        );

        self.client.force_login(
            self.user1
        );
        response1 = self.manage_bookshelf(
            BookStatus.Status.READING
        );
        self.assertTrue(
            response0.status_code==
            response1.status_code==
            200
        );

        self.assertEqual(
            BookStatus.objects.filter(
                book=self.book
            ).count(),
            2
        );

        self.assertEqual(
            BookStatus.objects.filter(
                book=self.book,
                status=BookStatus.Status.READING
            ).count(),
            1
        );
    def test_coexistent_equ_statuses(self):
        self.client.force_login(
            self.author_user
        );
        response0 = self.manage_bookshelf(
            BookStatus.Status.READ
        );

        self.client.force_login(
            self.user1
        );
        response1 = self.manage_bookshelf(
            BookStatus.Status.READ
        );
        self.assertTrue(
            response0.status_code==
            response1.status_code==
            200
        );

        self.assertEqual(
            BookStatus.objects.filter(
                book=self.book,
                status=BookStatus.Status.READ
            ).count(),
            2
        );

    def test_invalid_status(self):
        invalid_status = "I_HATE_BOOKS";

        self.client.force_login(
            self.author_user
        );

        response = self.manage_bookshelf(
            invalid_status
        );

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            BookStatus.objects.filter(
                status=invalid_status
            ).exists()
        );

    def test_reading_session_persistance(self):
        b_status = BookStatus.objects.create(
            user=self.user1,
            book=self.book,
            status=BookStatus.Status.READING
        );

        session = ReadingSession.objects.create(
            user=self.user1,
            book=self.book,
            pages_read=5,
            minute_count=10
        );
        session_id = session.id;

        response = self.manage_bookshelf();

        self.assertTrue(
            ReadingSession.objects.filter(
                id=session_id
            ).exists()
        );

# Testes de validação dos dados do registro
class ReadingSessionModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="leitor",
            email="leitor@email.com",
            password="senha123"
        )

        self.other_user = User.objects.create_user(
            username="outro_leitor",
            email="outro@email.com",
            password="senha123"
        )

        self.book = Book.objects.create(
            isbn="9780590353403",
            title="Livro de Teste",
            author="Autor Teste",
            genre="Ficção",
            pages=100
        )

    def test_registro_valido(self):
        session = ReadingSession(
            user=self.user,
            book=self.book,
            pages_read=20,
            minute_count=30,
            date=date(2026, 11, 4)
        )

        session.full_clean()

        self.assertEqual(session.pages_read, 20)

    def test_paginas_lidas_zero_e_invalido(self):
        session = ReadingSession(
            user=self.user,
            book=self.book,
            pages_read=0,
            minute_count=30
        )

        with self.assertRaises(ValidationError):
            session.full_clean()

    def test_paginas_lidas_maior_que_total_do_livro(self):
        session = ReadingSession(
            user=self.user,
            book=self.book,
            pages_read=110,
            minute_count=30
        )

        with self.assertRaises(ValidationError) as ctx:
            session.full_clean()

        self.assertIn("pages_read", ctx.exception.message_dict)

    def test_sessoes_seguidas_do_mesmo_livro_sao_permitidas(self):
        # cada sessão guarda só as páginas lidas nela (não há intervalo)
        ReadingSession.objects.create(
            user=self.user,
            book=self.book,
            pages_read=10,
            minute_count=30
        )

        session = ReadingSession(
            user=self.user,
            book=self.book,
            pages_read=10,
            minute_count=20
        )

        session.full_clean()

    def test_outro_usuario_pode_registrar_as_mesmas_paginas(self):
        ReadingSession.objects.create(
            user=self.user,
            book=self.book,
            pages_read=10,
            minute_count=30
        )

        session = ReadingSession(
            user=self.other_user,
            book=self.book,
            pages_read=10,
            minute_count=20
        )

        session.full_clean()


# Testes de validação do formulário de registro
class ReadingSessionFormTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="leitor",
            email="leitor@email.com",
            password="senha123"
        )

        self.book = Book.objects.create(
            isbn="9780590353403",
            title="Livro de Teste",
            author="Autor Teste",
            genre="Ficção",
            pages=100
        )

    def form_data(self, **overrides):
        data = {
            "book": self.book.id,
            "current_page": 20,
            "minute_count": 30,
            "date": "2026-11-04"
        }
        data.update(overrides)
        return data

    def test_formulario_valido_com_pagina_atual(self):
        form = ReadingSessionForm(data=self.form_data(), user=self.user)

        self.assertTrue(form.is_valid(), form.errors)

    def test_formulario_valido_com_percentual(self):
        data = self.form_data(current_percentage="50")
        del data["current_page"]
        form = ReadingSessionForm(data=data, user=self.user)

        self.assertTrue(form.is_valid(), form.errors)

    def test_formulario_exige_pagina_ou_percentual(self):
        data = self.form_data()
        del data["current_page"]
        form = ReadingSessionForm(data=data, user=self.user)

        self.assertFalse(form.is_valid())

    def test_formulario_impede_pagina_e_percentual_juntos(self):
        form = ReadingSessionForm(
            data=self.form_data(current_percentage="50"),
            user=self.user
        )

        self.assertFalse(form.is_valid())

    def test_formulario_impede_pagina_maior_que_total_do_livro(self):
        form = ReadingSessionForm(
            data=self.form_data(current_page=110),
            user=self.user
        )

        self.assertFalse(form.is_valid())
        self.assertIn("current_page", form.errors)


# Testes da view de registro de leitura
class ReadingSessionViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="leitor",
            email="leitor@email.com",
            password="senha123"
        )

        self.book = Book.objects.create(
            isbn="9780590353403",
            title="Livro de Teste",
            author="Autor Teste",
            genre="Ficção",
            pages=100
        )

        self.url = reverse("books:register_reading_session")

    def test_usuario_autenticado_registra_sessao(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, {
            "book": self.book.id,
            "current_page": 20,
            "minute_count": 30,
            "date": "2026-11-04"
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ReadingSession.objects.count(), 1)

        session = ReadingSession.objects.first()

        self.assertEqual(session.user, self.user)
        self.assertEqual(session.book, self.book)
        self.assertEqual(session.pages_read, 20)

    def test_pagina_atual_e_acumulada_entre_sessoes(self):
        self.client.force_login(self.user)

        for current_page in (20, 30):
            self.client.post(self.url, {
                "book": self.book.id,
                "current_page": current_page,
                "minute_count": 30,
                "date": "2026-11-04"
            })

        # a 2ª sessão leu só as páginas que faltavam: 30 - 20
        pages = list(
            ReadingSession.objects.order_by("id")
            .values_list("pages_read", flat=True)
        )
        self.assertEqual(pages, [20, 10])

    def test_progresso_menor_ou_igual_ao_anterior_e_rejeitado(self):
        self.client.force_login(self.user)
        self.client.post(self.url, {
            "book": self.book.id,
            "current_page": 20,
            "minute_count": 30,
            "date": "2026-11-04"
        })

        response = self.client.post(self.url, {
            "book": self.book.id,
            "current_page": 20,
            "minute_count": 30,
            "date": "2026-11-04"
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ReadingSession.objects.count(), 1)

    def test_usuario_nao_autenticado_nao_acessa_registro(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ReadingSession.objects.count(), 0)

class ReadingSessionStreakViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="leitor", email="leitor@email.com", password="senha123")
        self.book = Book.objects.create(
            isbn="9780590353403", title="Livro de Teste",
            author="Autor Teste", genre="Ficção", pages=100)
        self.url = reverse("books:register_reading_session")
        self.client.force_login(self.user)
        self.today = timezone.localdate()

    def post_session(self, current_page, day=None):
        # current_page é a página em que o leitor parou (acumulada no livro)
        return self.client.post(self.url, {
            "book": self.book.id,
            "current_page": current_page,
            "minute_count": 30,
            "date": (day or self.today).isoformat(),
        })

    def streak(self):
        # o Profile é criado sob demanda (get_or_create na view): se nenhuma
        # leitura foi salva, ele não existe e a ofensiva é 0
        profile = Profile.objects.filter(user=self.user).first()
        return profile.streak if profile else 0

    def test_primeira_sessao_define_ofensiva_em_1(self):
        response = self.post_session(10)

        self.assertEqual(response.status_code, 302)
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.streak, 1)
        self.assertEqual(profile.last_read_date, self.today)

    def test_ofensiva_incrementa_a_cada_dia(self):
        self.post_session(10, day=self.today - timedelta(days=1))
        self.assertEqual(self.streak(), 1)

        self.post_session(20, day=self.today)
        self.assertEqual(self.streak(), 2)

    def test_varias_sessoes_no_mesmo_dia_contam_uma_vez(self):
        self.post_session(10)
        self.post_session(20)
        self.post_session(30)

        self.assertEqual(ReadingSession.objects.count(), 3)
        self.assertEqual(self.streak(), 1)

    def test_faltar_um_dia_reseta_a_ofensiva(self):
        profile = Profile.objects.create(
            user=self.user, streak=5,
            last_read_date=self.today - timedelta(days=3))

        self.post_session(10)

        profile.refresh_from_db()
        # zerou por causa da falta e recomeçou em 1 com a leitura de hoje
        self.assertEqual(profile.streak, 1)
        self.assertEqual(profile.last_read_date, self.today)

    def test_data_futura_e_rejeitada_e_nao_altera_ofensiva(self):
        response = self.post_session(10, day=self.today + timedelta(days=1))

        self.assertEqual(response.status_code, 200)
        self.assertIn("date", response.context["form"].errors)
        self.assertEqual(ReadingSession.objects.count(), 0)
        self.assertEqual(self.streak(), 0)

    def test_sessao_com_data_futura_falha_na_validacao_do_modelo(self):
        session = ReadingSession(
            user=self.user, book=self.book, pages_read=10,
            minute_count=30, date=self.today + timedelta(days=1))

        with self.assertRaises(ValidationError) as ctx:
            session.full_clean()

        self.assertIn("date", ctx.exception.message_dict)

# Testes de atualização do BookStatus e contribuição nas metas
class ReadingSessionProgressAndGoalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="leitor_progresso",
            password="senha123"
        )

        self.profile = Profile.objects.create(user=self.user)

        self.book = Book.objects.create(
            isbn="9780590353403",
            title="Livro de Teste",
            author="Autor Teste",
            genre="Ficção",
            pages=100
        )

        self.url = reverse("books:register_reading_session")
        self.client.force_login(self.user)

    def post_session(self, current_page, minute_count=30):
        return self.client.post(self.url, {
            "book": self.book.id,
            "current_page": current_page,
            "minute_count": minute_count,
            "date": timezone.localdate().isoformat()
        })

    def test_registro_inicia_bookstatus_com_status_lendo(self):
        self.post_session(20)

        book_status = BookStatus.objects.get(
            user=self.user,
            book=self.book
        )

        self.assertEqual(
            book_status.status,
            BookStatus.Status.READING
        )

    def test_progresso_bookstatus_acumula_corretamente(self):
        self.post_session(20)
        self.post_session(34)

        book_status = BookStatus.objects.get(
            user=self.user,
            book=self.book
        )

        self.assertEqual(
            book_status.reading_progress,
            Decimal("0.340")
        )

    def test_bookstatus_muda_para_lido_ao_completar_livro(self):
        BookStatus.objects.create(
            user=self.user,
            book=self.book,
            status=BookStatus.Status.READING,
            reading_progress=Decimal("0.900")
        )

        self.post_session(100)

        book_status = BookStatus.objects.get(
            user=self.user,
            book=self.book
        )

        self.assertEqual(
            book_status.reading_progress,
            Decimal("1.000")
        )

        self.assertEqual(
            book_status.status,
            BookStatus.Status.READ
        )

    def test_registro_contribui_para_meta_de_paginas(self):
        goal = Goal.objects.create(
            name="Ler 50 páginas",
            owner_profile=self.profile,
            goal_type=Goal.GoalType.PAGE_COUNT,
            target=50,
            book=self.book
        )

        participation = GoalParticipation.objects.create(
            user=self.user,
            goal=goal,
            joined_at=timezone.now() - timedelta(days=1)
        )

        self.post_session(20)
        self.post_session(34)

        contribution = GoalService.get_user_contribution(
            participation
        )

        self.assertEqual(contribution, 34)

    def test_registro_contribui_para_meta_de_horas(self):
        goal = Goal.objects.create(
            name="Ler por 2 horas",
            owner_profile=self.profile,
            goal_type=Goal.GoalType.HOUR_COUNT,
            target=120,
            book=self.book
        )

        participation = GoalParticipation.objects.create(
            user=self.user,
            goal=goal,
            joined_at=timezone.now() - timedelta(days=1)
        )

        self.post_session(20, minute_count=30)
        self.post_session(34, minute_count=40)

        contribution = GoalService.get_user_contribution(
            participation
        )

        self.assertEqual(contribution, 70)

    def test_leitura_anterior_a_entrada_na_meta_nao_contribui(self):
        goal = Goal.objects.create(
            name="Ler 50 páginas",
            owner_profile=self.profile,
            goal_type=Goal.GoalType.PAGE_COUNT,
            target=50,
            book=self.book
        )

        participation = GoalParticipation.objects.create(
            user=self.user,
            goal=goal,
            joined_at=timezone.now()
        )

        # Registra uma leitura com data anterior à entrada na meta
        ReadingSession.objects.create(
            user=self.user,
            book=self.book,
            pages_read=20,
            minute_count=30,
            date=timezone.localdate() - timedelta(days=2)
        )

        contribution = GoalService.get_user_contribution(
            participation
        )

        self.assertEqual(contribution, 0)


class SaveReadingSessionViewTests(TestCase):
    """Persistência das sessões feitas na tela "Registrar leitura" (JSON)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="leitor_json",
            email="leitor_json@email.com",
            password="senha123"
        )
        self.book = Book.objects.create(
            isbn="9780590353403",
            title="Livro de Teste",
            author="Autor Teste",
            pages=100
        )
        self.url = reverse("books:save_reading_session", args=[self.book.id])

    def post(self, payload, url=None):
        return self.client.post(
            url or self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )

    def test_salva_sessao_no_banco(self):
        self.client.force_login(self.user)

        response = self.post({"pages_read": 20, "minute_count": 30})

        self.assertEqual(response.status_code, 200)
        session = ReadingSession.objects.get()
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.book, self.book)
        self.assertEqual(session.pages_read, 20)
        self.assertEqual(session.minute_count, 30)
        self.assertEqual(session.date, timezone.localdate())

    def test_atualiza_ofensiva(self):
        self.client.force_login(self.user)

        self.post({"pages_read": 5, "minute_count": 10})

        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.streak, 1)
        self.assertEqual(profile.last_read_date, timezone.localdate())

    def test_usuario_anonimo_nao_salva(self):
        response = self.post({"pages_read": 5, "minute_count": 10})

        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(ReadingSession.objects.count(), 0)

    def test_exige_metodo_post(self):
        self.client.force_login(self.user)

        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_dados_invalidos_sao_rejeitados(self):
        self.client.force_login(self.user)

        for payload in (
            {},
            {"pages_read": "abc", "minute_count": 10},
            {"pages_read": 0, "minute_count": 10},
            {"pages_read": 5, "minute_count": 0},
            {"pages_read": 5, "minute_count": 1441},
        ):
            with self.subTest(payload=payload):
                self.assertEqual(self.post(payload).status_code, 400)

        self.assertEqual(ReadingSession.objects.count(), 0)

    def test_livro_inexistente_retorna_404(self):
        self.client.force_login(self.user)
        url = reverse("books:save_reading_session", args=[9999])

        self.assertEqual(
            self.post({"pages_read": 5, "minute_count": 10}, url).status_code, 404
        )

    def test_livro_sem_paginas_e_rejeitado(self):
        self.client.force_login(self.user)
        self.book.pages = None
        self.book.save()

        self.assertEqual(
            self.post({"pages_read": 5, "minute_count": 10}).status_code, 400
        )
        self.assertEqual(ReadingSession.objects.count(), 0)

    def test_limita_ao_total_de_paginas_do_livro(self):
        self.client.force_login(self.user)
        ReadingSession.objects.create(
            user=self.user, book=self.book, pages_read=99, minute_count=60
        )

        response = self.post({"pages_read": 5, "minute_count": 10})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["pages_read"], 1)

        # livro já todo registrado: nada mais é gravado
        self.assertEqual(
            self.post({"pages_read": 1, "minute_count": 5}).status_code, 400
        )
        self.assertEqual(ReadingSession.objects.count(), 2)


class ReadingSessionDataModelTests(TestCase):
    """Fase 1: novos campos de ReadingSession, backfill da migration e
    sessões sem pages_read (livros sem total de páginas)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="leitor_dados",
            password="senha123"
        )
        self.other_user = User.objects.create_user(
            username="outro_dados",
            password="senha123"
        )
        self.profile = Profile.objects.create(user=self.user)

        self.book = Book.objects.create(
            isbn="9780590353403",
            title="Livro com páginas",
            author="Autor",
            genre="Ficção",
            pages=100
        )
        self.other_book = Book.objects.create(
            isbn="9780747532743",
            title="Outro livro",
            author="Autor",
            genre="Ficção",
            pages=200
        )
        # livro sem total de páginas: sessões usam record_type="percent"
        self.book_no_pages = Book.objects.create(
            isbn="9780261103573",
            title="Livro sem total",
            author="Autor",
            genre="Ficção",
            pages=None
        )

    def make_percent_session(self, percent, minutes=20, **extra):
        return ReadingSession.objects.create(
            user=self.user,
            book=self.book_no_pages,
            pages_read=None,
            minute_count=minutes,
            record_type="percent",
            stopped_percent=Decimal(percent),
            cumulative_percent=Decimal(percent),
            **extra
        )

    # ---------- campos novos ----------
    def test_defaults_dos_novos_campos(self):
        session = ReadingSession.objects.create(
            user=self.user, book=self.book, pages_read=10, minute_count=15
        )
        self.assertEqual(session.record_type, "pages")
        self.assertIsNotNone(session.created_at)
        self.assertIsNone(session.stopped_percent)
        self.assertIsNone(session.cumulative_percent)

    def test_created_at_tem_hora_e_indice(self):
        field = ReadingSession._meta.get_field("created_at")
        self.assertTrue(field.db_index)
        session = ReadingSession.objects.create(
            user=self.user, book=self.book, pages_read=10, minute_count=15
        )
        self.assertTrue(hasattr(session.created_at, "hour"))

    def test_save_calcula_cumulative_pages_por_usuario_e_livro(self):
        first = ReadingSession.objects.create(
            user=self.user, book=self.book, pages_read=10, minute_count=10
        )
        second = ReadingSession.objects.create(
            user=self.user, book=self.book, pages_read=25, minute_count=10
        )
        # outro livro e outro usuário não interferem no acumulado
        other_book_session = ReadingSession.objects.create(
            user=self.user, book=self.other_book, pages_read=7, minute_count=10
        )
        other_user_session = ReadingSession.objects.create(
            user=self.other_user, book=self.book, pages_read=3, minute_count=10
        )

        self.assertEqual(first.cumulative_pages, 10)
        self.assertEqual(first.stopped_page, 10)
        self.assertEqual(second.cumulative_pages, 35)
        self.assertEqual(second.stopped_page, 35)
        self.assertEqual(other_book_session.cumulative_pages, 7)
        self.assertEqual(other_user_session.cumulative_pages, 3)

    def test_save_nao_sobrescreve_cumulative_informado(self):
        session = ReadingSession.objects.create(
            user=self.user, book=self.book, pages_read=10, minute_count=10,
            cumulative_pages=50, stopped_page=50
        )
        self.assertEqual(session.cumulative_pages, 50)
        self.assertEqual(session.stopped_page, 50)

    # ---------- sessão com pages_read nulo ----------
    def test_sessao_em_percentual_aceita_pages_read_nulo(self):
        session = self.make_percent_session("35.50")
        session.full_clean()  # não deve levantar ValidationError
        session.refresh_from_db()

        self.assertIsNone(session.pages_read)
        self.assertEqual(session.record_type, "percent")
        self.assertEqual(session.stopped_percent, Decimal("35.50"))
        self.assertEqual(session.cumulative_percent, Decimal("35.50"))
        # save() não inventa acumulado de páginas para sessões em percentual
        self.assertIsNone(session.cumulative_pages)
        self.assertIsNone(session.stopped_page)

    # ---------- backfill da migration ----------
    def test_backfill_preenche_sessoes_existentes(self):
        migration = importlib.import_module("books.migrations.0002_readingsession_record_fields")
        today = timezone.localdate()

        # cria sessões "antigas": sem os campos novos preenchidos
        s1 = ReadingSession.objects.create(
            user=self.user, book=self.book, pages_read=10, minute_count=10,
            date=today - timedelta(days=3)
        )
        s2 = ReadingSession.objects.create(
            user=self.user, book=self.book, pages_read=20, minute_count=10,
            date=today - timedelta(days=1)
        )
        # mesma data de s3, id maior: desempate por id
        s3 = ReadingSession.objects.create(
            user=self.user, book=self.book, pages_read=5, minute_count=10,
            date=today - timedelta(days=1)
        )
        o1 = ReadingSession.objects.create(
            user=self.user, book=self.other_book, pages_read=8, minute_count=10,
            date=today - timedelta(days=2)
        )
        u1 = ReadingSession.objects.create(
            user=self.other_user, book=self.book, pages_read=4, minute_count=10,
            date=today - timedelta(days=2)
        )

        # simula o estado pré-migration
        ReadingSession.objects.update(
            created_at=timezone.now(), record_type="percent",
            cumulative_pages=None, stopped_page=None
        )

        migration.backfill_reading_sessions(django_apps, None)

        for s in (s1, s2, s3, o1, u1):
            s.refresh_from_db()

        self.assertEqual([s1.cumulative_pages, s2.cumulative_pages, s3.cumulative_pages], [10, 30, 35])
        self.assertEqual(o1.cumulative_pages, 8)
        self.assertEqual(u1.cumulative_pages, 4)

        for s in (s1, s2, s3, o1, u1):
            self.assertEqual(s.record_type, "pages")
            self.assertEqual(s.stopped_page, s.cumulative_pages)
            # created_at = meia-noite local da data da sessão
            local = timezone.localtime(s.created_at)
            self.assertEqual(local.date(), s.date)
            self.assertEqual((local.hour, local.minute, local.second), (0, 0, 0))

    # ---------- metas ----------
    def test_meta_de_paginas_ignora_sessao_com_pages_read_nulo(self):
        goal = Goal.objects.create(
            name="Ler 50 páginas",
            owner_profile=self.profile,
            goal_type=Goal.GoalType.PAGE_COUNT,
            target=50
        )
        participation = GoalParticipation.objects.create(
            user=self.user, goal=goal,
            joined_at=timezone.now() - timedelta(days=1)
        )
        ReadingSession.objects.create(
            user=self.user, book=self.book, pages_read=12, minute_count=10
        )
        self.make_percent_session("40")

        self.assertEqual(GoalService.get_user_contribution(participation), 12)
        self.assertEqual(GoalService.get_individual_progress(goal)["current"], 12)

    def test_meta_de_horas_conta_sessao_com_pages_read_nulo(self):
        goal = Goal.objects.create(
            name="Ler 2 horas",
            owner_profile=self.profile,
            goal_type=Goal.GoalType.HOUR_COUNT,
            target=120
        )
        participation = GoalParticipation.objects.create(
            user=self.user, goal=goal,
            joined_at=timezone.now() - timedelta(days=1)
        )
        ReadingSession.objects.create(
            user=self.user, book=self.book, pages_read=12, minute_count=10
        )
        self.make_percent_session("40", minutes=25)

        self.assertEqual(GoalService.get_user_contribution(participation), 35)
        self.assertEqual(GoalService.get_individual_progress(goal)["current"], 35)

    def test_meta_de_paginas_so_com_sessoes_em_percentual_da_zero(self):
        goal = Goal.objects.create(
            name="Ler 50 páginas",
            owner_profile=self.profile,
            goal_type=Goal.GoalType.PAGE_COUNT,
            target=50
        )
        participation = GoalParticipation.objects.create(
            user=self.user, goal=goal,
            joined_at=timezone.now() - timedelta(days=1)
        )
        self.make_percent_session("40")

        self.assertEqual(GoalService.get_user_contribution(participation), 0)
        self.assertEqual(GoalService.get_individual_progress(goal)["current"], 0)

    # ---------- histórico do dia (accounts) ----------
    def test_historico_do_dia_lida_com_pages_read_nulo(self):
        self.make_percent_session("40", minutes=25)
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("accounts:streak_day_history", args=[timezone.localdate().isoformat()])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_pages"], 0)
        self.assertEqual(response.context["total_minutes"], 25)


# ---------------------------------------------------------------------------
# Fase 2: endpoints JSON de sessões (CREATE / LIST / EDIT)
# ---------------------------------------------------------------------------
def days_ago(days, hour=12):
    """created_at ISO 8601 (fuso local) de N dias atrás, às `hour` horas."""
    base = timezone.localtime().replace(hour=hour, minute=0, second=0, microsecond=0)
    return (base - timedelta(days=days)).isoformat()


class SessionApiBase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="leitor_api", password="senha123")
        self.other = User.objects.create_user(username="outro_api", password="senha123")
        self.book = Book.objects.create(
            isbn="9780590353403", title="Livro com páginas", author="Autor", pages=100)
        self.book_no_pages = Book.objects.create(
            isbn="9780261103573", title="Livro sem total", author="Autor", pages=None)
        self.client.force_login(self.user)

    # --- urls ---
    def create_url(self, book=None):
        return reverse("books:save_reading_session", args=[(book or self.book).id])

    def list_url(self, book=None):
        return reverse("books:list_reading_sessions", args=[(book or self.book).id])

    def edit_url(self, session_id, book=None):
        return reverse("books:edit_reading_session", args=[(book or self.book).id, session_id])

    # --- chamadas ---
    def send(self, method, url, payload=None):
        return getattr(self.client, method)(
            url, data=json.dumps(payload or {}), content_type="application/json")

    def create(self, payload, book=None):
        return self.send("post", self.create_url(book), payload)

    def edit(self, session_id, payload, book=None, method="post"):
        return self.send(method, self.edit_url(session_id, book), payload)

    def create_ok(self, pages=None, percent=None, minutes=20, at=None, book=None):
        payload = {"minute_count": minutes}
        if pages is not None:
            payload["pages_read"] = pages
        if percent is not None:
            payload["stopped_percent"] = percent
        if at is not None:
            payload["created_at"] = at
        response = self.create(payload, book)
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def rows(self, book=None, user=None):
        return list(
            ReadingSession.objects.filter(user=user or self.user, book=book or self.book)
            .order_by("created_at", "id")
        )

    def cumulatives(self, book=None, user=None):
        return [s.cumulative_pages for s in self.rows(book, user)]

    def profile(self):
        return Profile.objects.get(user=self.user)


class CreateReadingSessionApiTests(SessionApiBase):
    def test_cria_sessao_de_paginas_com_acumulados_e_devolve_historico(self):
        self.create_ok(pages=20, minutes=30)
        body = self.create_ok(pages=15, minutes=10)

        self.assertEqual(self.cumulatives(), [20, 35])
        session = body["session"]
        self.assertEqual(session["record_type"], "pages")
        self.assertEqual(session["pages_read"], 15)
        self.assertEqual(session["stopped_page"], 35)
        self.assertEqual(session["cumulative_pages"], 35)
        self.assertEqual(session["cumulative_percent"], 35.0)
        self.assertEqual(session["date"], timezone.localdate().isoformat())
        # histórico atualizado, da mais antiga para a mais recente
        self.assertEqual([s["cumulative_pages"] for s in body["sessions"]], [20, 35])
        self.assertEqual(body["book_status"]["status"], "READING")
        self.assertEqual(body["book_status"]["progress"], 35)
        self.assertEqual(body["streak"]["current"], 1)
        # chaves legadas continuam presentes
        self.assertEqual(body["pages_read"], 15)
        self.assertEqual(body["id"], session["id"])

    def test_percentual_em_livro_com_paginas_vira_paginas_lidas(self):
        self.create_ok(percent=40)
        body = self.create_ok(percent=55.5)

        first, second = self.rows()
        self.assertEqual((first.record_type, first.pages_read, first.cumulative_pages), ("percent", 40, 40))
        self.assertEqual((second.pages_read, second.cumulative_pages), (16, 56))
        self.assertEqual(body["session"]["cumulative_percent"], 56.0)

    def test_percentual_que_nao_avanca_e_rejeitado_em_livro_com_paginas(self):
        self.create_ok(percent=40)

        for percent in (40, 30):
            with self.subTest(percent=percent):
                self.assertEqual(self.create({"stopped_percent": percent, "minute_count": 10}).status_code, 400)
        self.assertEqual(len(self.rows()), 1)

    def test_livro_sem_paginas_grava_percentual_e_sincroniza_bookstatus(self):
        self.create_ok(percent=25, book=self.book_no_pages)
        body = self.create_ok(percent=60, book=self.book_no_pages)

        first, second = self.rows(self.book_no_pages)
        self.assertIsNone(first.pages_read)
        self.assertEqual(first.record_type, "percent")
        self.assertEqual((first.stopped_percent, first.cumulative_percent), (Decimal("25.00"), Decimal("25.00")))
        self.assertIsNone(second.cumulative_pages)
        self.assertEqual(second.cumulative_percent, Decimal("60.00"))
        self.assertEqual(body["book_status"]["progress"], 60)

        book_status = BookStatus.objects.get(user=self.user, book=self.book_no_pages)
        self.assertEqual(book_status.reading_progress, Decimal("0.600"))
        self.assertEqual(book_status.status, BookStatus.Status.READING)

        self.create_ok(percent=100, book=self.book_no_pages)
        book_status.refresh_from_db()
        self.assertEqual(book_status.status, BookStatus.Status.READ)
        self.assertEqual(book_status.reading_progress, Decimal("1.000"))
        self.assertEqual(book_status.finished_at, timezone.localdate())

    def test_livro_sem_paginas_exige_percentual_e_que_ele_avance(self):
        for payload in (
            {"pages_read": 5, "minute_count": 10},
            {"record_type": "pages", "pages_read": 5, "minute_count": 10},
        ):
            with self.subTest(payload=payload):
                response = self.create(payload, self.book_no_pages)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["field"], "record_type")

        self.create_ok(percent=50, book=self.book_no_pages)
        for percent in (50, 40):
            with self.subTest(percent=percent):
                self.assertEqual(
                    self.create({"stopped_percent": percent, "minute_count": 10}, self.book_no_pages).status_code, 400)
        self.assertEqual(len(self.rows(self.book_no_pages)), 1)

    def test_created_at_opcional_define_data_e_ordem(self):
        body = self.create_ok(pages=10, at=days_ago(2))

        self.assertEqual(body["session"]["date"], (timezone.localdate() - timedelta(days=2)).isoformat())
        self.assertEqual(self.rows()[0].date, timezone.localdate() - timedelta(days=2))
        # só a data também é aceita
        body = self.create_ok(pages=5, at=(timezone.localdate() - timedelta(days=1)).isoformat())
        self.assertEqual([s["pages_read"] for s in body["sessions"]], [10, 5])

    def test_sessao_retroativa_no_meio_recalcula_a_cascata(self):
        self.create_ok(pages=10, at=days_ago(3))
        self.create_ok(pages=20, at=days_ago(1))
        self.assertEqual(self.cumulatives(), [10, 30])

        body = self.create_ok(pages=5, at=days_ago(2))

        self.assertEqual([s.pages_read for s in self.rows()], [10, 5, 20])
        self.assertEqual(self.cumulatives(), [10, 15, 35])
        self.assertEqual([s["cumulative_pages"] for s in body["sessions"]], [10, 15, 35])
        self.assertEqual(BookStatus.objects.get(user=self.user, book=self.book).reading_progress, Decimal("0.350"))

    def test_inserir_no_meio_acima_do_total_do_livro_e_rejeitado_sem_gravar(self):
        self.create_ok(pages=60, at=days_ago(3))
        self.create_ok(pages=30, at=days_ago(1))

        response = self.create({"pages_read": 20, "minute_count": 10, "created_at": days_ago(2)})

        self.assertEqual(response.status_code, 400)
        self.assertEqual([s.pages_read for s in self.rows()], [60, 30])
        self.assertEqual(self.cumulatives(), [60, 90])

    def test_bookstatus_vira_lido_ao_completar(self):
        body = self.create_ok(pages=100)

        self.assertEqual(body["book_status"]["status"], "READ")
        book_status = BookStatus.objects.get(user=self.user, book=self.book)
        self.assertEqual(book_status.reading_progress, Decimal("1.000"))
        self.assertEqual(book_status.finished_at, timezone.localdate())

    def test_sessao_retroativa_que_liga_dias_refaz_a_ofensiva(self):
        self.create_ok(pages=5, at=days_ago(2))
        self.create_ok(pages=5)  # hoje: o buraco do dia -1 quebra a ofensiva
        self.assertEqual(self.profile().streak, 1)

        body = self.create_ok(pages=5, at=days_ago(1))

        self.assertEqual(self.profile().streak, 3)
        self.assertEqual(body["streak"]["current"], 3)

    def test_validacoes_do_servidor(self):
        invalid = {
            "sem corpo": {},
            "sem tempo": {"pages_read": 5},
            "pages_read texto": {"pages_read": "abc", "minute_count": 10},
            "pages_read zero": {"pages_read": 0, "minute_count": 10},
            "acima do total": {"pages_read": 101, "minute_count": 10},
            "minutos zero": {"pages_read": 5, "minute_count": 0},
            "mais de 24h": {"pages_read": 5, "minute_count": 1441},
            "record_type invalido": {"record_type": "livro", "pages_read": 5, "minute_count": 10},
            "pages e percent juntos": {"pages_read": 5, "stopped_percent": 10, "minute_count": 10},
            "pages com record percent": {"record_type": "percent", "pages_read": 5, "minute_count": 10},
            "percent com record pages": {"record_type": "pages", "stopped_percent": 5, "minute_count": 10},
            "percent zero": {"stopped_percent": 0, "minute_count": 10},
            "percent acima de 100": {"stopped_percent": 100.5, "minute_count": 10},
            "created_at invalido": {"pages_read": 5, "minute_count": 10, "created_at": "ontem"},
            "created_at futuro": {
                "pages_read": 5, "minute_count": 10,
                "created_at": (timezone.localtime() + timedelta(days=2)).isoformat()},
        }
        for name, payload in invalid.items():
            with self.subTest(name):
                response = self.create(payload)
                self.assertEqual(response.status_code, 400)
                self.assertFalse(response.json()["success"])

        # limites válidos
        self.create_ok(pages=100, minutes=1440)
        self.assertEqual(ReadingSession.objects.count(), 1)

    def test_corpo_que_nao_e_json_e_rejeitado(self):
        response = self.client.post(self.create_url(), data="{oi", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_acumulado_e_independente_por_usuario(self):
        self.create_ok(pages=20)
        self.client.force_login(self.other)
        self.create_ok(pages=7)

        self.assertEqual(self.cumulatives(user=self.user), [20])
        self.assertEqual(self.cumulatives(user=self.other), [7])

    def test_falha_no_meio_desfaz_tudo(self):
        with mock.patch("books.services._sync_streak", side_effect=RuntimeError("falha")):
            with self.assertRaises(RuntimeError):
                self.create({"pages_read": 10, "minute_count": 10})

        self.assertEqual(ReadingSession.objects.count(), 0)
        self.assertEqual(BookStatus.objects.count(), 0)

    def test_anonimo_e_metodo_errado(self):
        self.client.logout()
        self.assertEqual(self.create({"pages_read": 5, "minute_count": 10}).status_code, 302)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.create_url()).status_code, 405)
        self.assertEqual(ReadingSession.objects.count(), 0)


class ListReadingSessionsApiTests(SessionApiBase):
    def test_lista_ordenada_por_created_at_com_acumulados(self):
        # criadas fora de ordem: a lista segue created_at, não o id
        self.create_ok(pages=20, at=days_ago(1))
        self.create_ok(pages=10, at=days_ago(3))
        self.create_ok(pages=5, at=days_ago(2))

        response = self.client.get(self.list_url())

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["pages"], 100)
        self.assertEqual([s["pages_read"] for s in body["sessions"]], [10, 5, 20])
        self.assertEqual([s["cumulative_pages"] for s in body["sessions"]], [10, 15, 35])
        self.assertEqual(body["book_status"]["progress"], 35)
        for key in ("id", "record_type", "minute_count", "stopped_page", "stopped_percent",
                    "cumulative_percent", "date", "created_at"):
            self.assertIn(key, body["sessions"][0])

    def test_lista_vazia(self):
        body = self.client.get(self.list_url()).json()

        self.assertEqual(body["sessions"], [])
        self.assertIsNone(body["book_status"])

    def test_nao_ve_sessoes_de_outro_usuario_nem_de_outro_livro(self):
        self.create_ok(pages=20)
        self.create_ok(percent=30, book=self.book_no_pages)
        self.client.force_login(self.other)
        self.create_ok(pages=9)

        mine = self.client.get(self.list_url()).json()["sessions"]
        self.client.force_login(self.user)
        yours = self.client.get(self.list_url()).json()["sessions"]

        self.assertEqual([s["pages_read"] for s in mine], [9])
        self.assertEqual([s["pages_read"] for s in yours], [20])

    def test_livro_inexistente_anonimo_e_metodo_errado(self):
        self.assertEqual(self.client.get(reverse("books:list_reading_sessions", args=[9999])).status_code, 404)
        self.assertEqual(self.client.post(self.list_url()).status_code, 405)
        self.client.logout()
        self.assertEqual(self.client.get(self.list_url()).status_code, 302)


class EditReadingSessionApiTests(SessionApiBase):
    def three_sessions(self):
        """Sessões de 10, 20 e 5 páginas em dias distintos (acumulados 10, 30, 35)."""
        a = self.create_ok(pages=10, at=days_ago(3))["session"]["id"]
        b = self.create_ok(pages=20, at=days_ago(2))["session"]["id"]
        c = self.create_ok(pages=5, at=days_ago(1))["session"]["id"]
        return a, b, c

    def test_editar_paginas_recalcula_acumulados_em_cascata(self):
        a, b, c = self.three_sessions()
        self.assertEqual(self.cumulatives(), [10, 30, 35])

        response = self.edit(b, {"pages_read": 30})

        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertEqual(self.cumulatives(), [10, 40, 45])
        self.assertEqual([s.pages_read for s in self.rows()], [10, 30, 5])
        self.assertEqual([s["cumulative_pages"] for s in body["sessions"]], [10, 40, 45])
        self.assertEqual(body["session"]["id"], b)
        self.assertEqual([s.stopped_page for s in self.rows()], [10, 40, 45])
        self.assertEqual(
            [s.cumulative_percent for s in self.rows()],
            [Decimal("10.00"), Decimal("40.00"), Decimal("45.00")])
        self.assertEqual(BookStatus.objects.get(user=self.user, book=self.book).reading_progress, Decimal("0.450"))

    def test_editar_a_primeira_sessao_empurra_todas_as_seguintes(self):
        a, b, c = self.three_sessions()

        self.edit(a, {"pages_read": 30})

        self.assertEqual(self.cumulatives(), [30, 50, 55])

    def test_editar_so_o_tempo_nao_mexe_nos_acumulados(self):
        a, b, c = self.three_sessions()

        response = self.edit(b, {"minute_count": 90}, method="patch")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ReadingSession.objects.get(pk=b).minute_count, 90)
        self.assertEqual(self.cumulatives(), [10, 30, 35])

    def test_editar_created_at_reordena_e_recalcula(self):
        a, b, c = self.three_sessions()

        # move a 1ª sessão (10 págs) para depois da 3ª
        response = self.edit(a, {"created_at": days_ago(0, hour=1)})

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual([s.pk for s in self.rows()], [b, c, a])
        self.assertEqual(self.cumulatives(), [20, 25, 35])
        self.assertEqual(ReadingSession.objects.get(pk=a).date, timezone.localdate())

    def test_editar_por_percentual_converte_relativo_a_sessao_anterior(self):
        a, b, c = self.three_sessions()  # acumulados 10, 30, 35

        response = self.edit(b, {"stopped_percent": 50})

        self.assertEqual(response.status_code, 200, response.content)
        edited = ReadingSession.objects.get(pk=b)
        self.assertEqual((edited.record_type, edited.pages_read, edited.cumulative_pages), ("percent", 40, 50))
        self.assertEqual(self.cumulatives(), [10, 50, 55])

        # percentual atrás da sessão anterior não avança
        self.assertEqual(self.edit(b, {"stopped_percent": 8}).status_code, 400)
        self.assertEqual(self.cumulatives(), [10, 50, 55])

    def test_editar_acima_do_total_do_livro_e_rejeitado_e_nada_muda(self):
        a = self.create_ok(pages=60, at=days_ago(2))["session"]["id"]
        self.create_ok(pages=30, at=days_ago(1))

        response = self.edit(a, {"pages_read": 80})  # 80 + 30 > 100

        self.assertEqual(response.status_code, 400)
        self.assertEqual([s.pages_read for s in self.rows()], [60, 30])
        self.assertEqual(self.cumulatives(), [60, 90])

    def test_livro_sem_paginas_percentual_fica_entre_vizinhas(self):
        ids = [
            self.create_ok(percent=percent, at=days_ago(days), book=self.book_no_pages)["session"]["id"]
            for percent, days in ((20, 3), (50, 2), (80, 1))
        ]
        middle = ids[1]

        self.assertEqual(self.edit(middle, {"stopped_percent": 90}, self.book_no_pages).status_code, 400)
        self.assertEqual(self.edit(middle, {"stopped_percent": 80}, self.book_no_pages).status_code, 400)
        self.assertEqual(self.edit(middle, {"stopped_percent": 20}, self.book_no_pages).status_code, 400)
        self.assertEqual(self.edit(middle, {"record_type": "pages", "pages_read": 5}, self.book_no_pages).status_code, 400)

        response = self.edit(middle, {"stopped_percent": 60}, self.book_no_pages)

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            [s.cumulative_percent for s in self.rows(self.book_no_pages)],
            [Decimal("20.00"), Decimal("60.00"), Decimal("80.00")])
        self.assertEqual(
            BookStatus.objects.get(user=self.user, book=self.book_no_pages).reading_progress, Decimal("0.800"))

    def test_bookstatus_e_ressincronizado_ao_reduzir_ou_completar(self):
        session_id = self.create_ok(pages=100)["session"]["id"]
        book_status = BookStatus.objects.get(user=self.user, book=self.book)
        self.assertEqual(book_status.status, BookStatus.Status.READ)

        self.edit(session_id, {"pages_read": 60})
        book_status.refresh_from_db()
        self.assertEqual(book_status.status, BookStatus.Status.READING)
        self.assertEqual(book_status.reading_progress, Decimal("0.600"))
        self.assertIsNone(book_status.finished_at)

        self.edit(session_id, {"pages_read": 100})
        book_status.refresh_from_db()
        self.assertEqual(book_status.status, BookStatus.Status.READ)
        self.assertEqual(book_status.reading_progress, Decimal("1.000"))
        self.assertIsNotNone(book_status.finished_at)

    def test_ofensiva_apos_editar_remove_dia_que_tinha_so_aquela_sessao(self):
        self.create_ok(pages=5, at=days_ago(2))
        middle = self.create_ok(pages=5, at=days_ago(1))["session"]["id"]
        self.create_ok(pages=5)
        self.assertEqual(self.profile().streak, 3)

        # mover a sessão do dia -1 para o dia -2 apaga o dia -1 da ofensiva
        response = self.edit(middle, {"created_at": days_ago(2, hour=13)})

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.profile().streak, 1)
        self.assertEqual(self.profile().last_read_date, timezone.localdate())
        self.assertEqual(response.json()["streak"]["current"], 1)

    def test_ofensiva_apos_editar_unica_sessao_para_dia_antigo_zera(self):
        session_id = self.create_ok(pages=5)["session"]["id"]
        self.assertEqual(self.profile().streak, 1)

        response = self.edit(session_id, {"created_at": days_ago(5)})

        self.assertEqual(response.status_code, 200)
        profile = self.profile()
        self.assertEqual(profile.streak, 0)  # leitura de 5 dias atrás não sustenta ofensiva
        self.assertEqual(profile.last_read_date, timezone.localdate() - timedelta(days=5))

    def test_ofensiva_considera_sessoes_de_todos_os_livros(self):
        self.create_ok(pages=5, at=days_ago(1))
        self.create_ok(pages=5)
        self.assertEqual(self.profile().streak, 2)  # dias -1 e 0 do livro com páginas

        # sessão retroativa em OUTRO livro (dia -2) liga-se à sequência
        other_book_session = self.create_ok(
            percent=10, at=days_ago(2), book=self.book_no_pages)["session"]["id"]
        self.assertEqual(self.profile().streak, 3)

        # editar a sessão do outro livro refaz a ofensiva com os dias dos DOIS livros
        self.edit(other_book_session, {"minute_count": 15}, self.book_no_pages)

        self.assertEqual(self.profile().streak, 3)

    def test_nao_edita_sessao_de_outro_usuario(self):
        a, b, c = self.three_sessions()
        self.client.force_login(self.other)

        response = self.edit(b, {"pages_read": 99})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(ReadingSession.objects.get(pk=b).pages_read, 20)
        self.assertEqual(self.cumulatives(user=self.user), [10, 30, 35])
        self.assertEqual(Profile.objects.filter(user=self.other).count(), 0)

    def test_sessao_de_outro_livro_ou_inexistente_da_404(self):
        a, b, c = self.three_sessions()

        self.assertEqual(self.edit(b, {"pages_read": 5}, self.book_no_pages).status_code, 404)
        self.assertEqual(self.edit(99999, {"pages_read": 5}).status_code, 404)

    def test_validacoes_na_edicao(self):
        a, b, c = self.three_sessions()
        invalid = {
            "sem campos": {},
            "acima do total": {"pages_read": 101},
            "pages_read zero": {"pages_read": 0},
            "minutos zero": {"minute_count": 0},
            "mais de 24h": {"minute_count": 1441},
            "record_type invalido": {"record_type": "x"},
            "trocar tipo sem valor": {"record_type": "percent"},
            "created_at futuro": {"created_at": (timezone.localtime() + timedelta(days=3)).isoformat()},
            "pages e percent": {"pages_read": 5, "stopped_percent": 30},
        }
        for name, payload in invalid.items():
            with self.subTest(name):
                self.assertEqual(self.edit(b, payload).status_code, 400)

        self.assertEqual(self.cumulatives(), [10, 30, 35])
        self.assertEqual(ReadingSession.objects.get(pk=b).minute_count, 20)

    def test_anonimo_e_metodo_errado(self):
        a, b, c = self.three_sessions()

        self.assertEqual(self.client.get(self.edit_url(b)).status_code, 405)
        self.client.logout()
        self.assertEqual(self.edit(b, {"pages_read": 5}).status_code, 302)
        self.assertEqual(ReadingSession.objects.get(pk=b).pages_read, 20)

    def test_falha_no_meio_da_edicao_desfaz_tudo(self):
        a, b, c = self.three_sessions()

        with mock.patch("books.services._sync_book_status", side_effect=RuntimeError("falha")):
            with self.assertRaises(RuntimeError):
                self.edit(b, {"pages_read": 30})

        self.assertEqual(ReadingSession.objects.get(pk=b).pages_read, 20)
        self.assertEqual(self.cumulatives(), [10, 30, 35])


class RegisterReadingSessionSharedHelperTests(SessionApiBase):
    """O form de reading/register/ usa o mesmo helper do endpoint JSON."""

    def setUp(self):
        super().setUp()
        self.url = reverse("books:register_reading_session")

    def post_form(self, **extra):
        data = {"book": self.book.id, "minute_count": 30, "date": timezone.localdate().isoformat()}
        data.update(extra)
        return self.client.post(self.url, data)

    def test_form_preenche_acumulados_bookstatus_e_ofensiva(self):
        self.assertEqual(self.post_form(current_page=20).status_code, 302)
        self.assertEqual(self.post_form(current_page=35).status_code, 302)

        self.assertEqual([s.pages_read for s in self.rows()], [20, 15])
        self.assertEqual(self.cumulatives(), [20, 35])
        self.assertEqual([s.stopped_page for s in self.rows()], [20, 35])
        self.assertEqual(self.rows()[-1].cumulative_percent, Decimal("35.00"))
        self.assertEqual(BookStatus.objects.get(user=self.user, book=self.book).reading_progress, Decimal("0.350"))
        self.assertEqual(self.profile().streak, 1)

    def test_form_com_percentual_grava_record_type_percent(self):
        self.assertEqual(self.post_form(current_percentage="40").status_code, 302)

        session = self.rows()[0]
        self.assertEqual((session.record_type, session.pages_read, session.cumulative_pages), ("percent", 40, 40))

    def test_form_com_data_passada_define_created_at_e_date(self):
        yesterday = timezone.localdate() - timedelta(days=1)

        self.assertEqual(self.post_form(current_page=10, date=yesterday.isoformat()).status_code, 302)

        session = self.rows()[0]
        self.assertEqual(session.date, yesterday)
        self.assertEqual(timezone.localtime(session.created_at).date(), yesterday)

    def test_sessao_do_form_aparece_na_lista_e_pode_ser_editada(self):
        self.post_form(current_page=20)
        self.post_form(current_page=50)
        first, second = self.rows()

        self.assertEqual(self.edit(first.pk, {"pages_read": 25}).status_code, 200)

        self.assertEqual(self.cumulatives(), [25, 55])
        listed = self.client.get(self.list_url()).json()["sessions"]
        self.assertEqual([s["cumulative_pages"] for s in listed], [25, 55])