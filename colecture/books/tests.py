import json;
import importlib

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
