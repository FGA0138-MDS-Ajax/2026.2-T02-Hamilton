import json;

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
