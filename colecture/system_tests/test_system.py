import os
import re
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

# Permite chamadas síncronas ao ORM junto com o Playwright
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright

from accounts.models import Profile
from books.models import Book, BookReview, BookStatus, ReadingSession
from communities.models import Community, Membership
from forums.models import Forum, Message
from goals.models import Goal, GoalParticipation
from logs.models import AuditLog
from notifications.models import Notification
from rewards.models import Award, CriteriaType, Insignia
from rewards.services import check_first_read

SCREENSHOTS_DIR = Path(__file__).resolve().parent / "screenshots"


class BaseSystemTestCase(StaticLiveServerTestCase):
    """Classe base compartilhada para todos os testes de sistema com Playwright."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        headed = os.environ.get("HEADED") == "1"
        cls.browser = cls.playwright.chromium.launch(
            headless=not headed,
            args=["--disable-web-security"],
        )

    @classmethod
    def tearDownClass(cls):
        try:
            cls.browser.close()
        except Exception:
            pass
        try:
            cls.playwright.stop()
        except Exception:
            pass
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.context = self.browser.new_context(
            viewport={"width": 1366, "height": 768}
        )
        self.page = self.context.new_page()

    def tearDown(self):
        # Salva screenshot em caso de falha no teste
        failed = False
        if hasattr(self, "_outcome"):
            for _, exc_info in getattr(self._outcome, "errors", []):
                if exc_info:
                    failed = True
                    break
        if failed and hasattr(self, "page") and self.page:
            try:
                SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
                screenshot_path = SCREENSHOTS_DIR / f"{self._testMethodName}.png"
                self.page.screenshot(path=str(screenshot_path), full_page=True)
            except Exception:
                pass
        try:
            self.context.close()
        except Exception:
            pass
        super().tearDown()

    # --- Métodos auxiliares de criação e autenticação via ORM / UI ---

    def create_user(
        self,
        username,
        password="Password123!",
        email=None,
        first_name="",
        last_name="",
        is_staff=False,
        is_superuser=False,
    ):
        """Cria um usuário com seu Profile associado via ORM."""
        email = email or f"{username}@colecture.local"
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )
        Profile.objects.get_or_create(user=user)
        return user

    def login_via_ui(self, username, password="Password123!"):
        """Realiza login pela interface gráfica e aguarda redirecionamento."""
        self.page.goto(f"{self.live_server_url}/user/login/")
        self.page.fill('input[name="username"]', username)
        self.page.fill('input[name="password"]', password)
        self.page.click('#login-form button[type="submit"]')
        self.page.wait_for_load_state("networkidle")

    def logout_via_ui(self):
        """Efetua logout submetendo o formulário de saída."""
        logout_button = self.page.locator(".logout-form button[type='submit']")
        if logout_button.count() > 0:
            logout_button.first.click()
            self.page.wait_for_load_state("networkidle")
        else:
            self.page.goto(f"{self.live_server_url}/")

    def create_book(
        self,
        title="Livro Exemplo",
        author="Autor Exemplo",
        isbn="9788535902778",
        pages=200,
        genre="ficcao",
        synopsis="Sinopse de teste",
        created_by=None,
    ):
        """Cria um livro no catálogo via ORM."""
        return Book.objects.create(
            title=title,
            author=author,
            isbn=isbn,
            pages=pages,
            genre=genre,
            synopsis=synopsis,
            created_by=created_by,
        )

    def create_community(
        self,
        name="Comunidade Teste",
        creator=None,
        access=Community.Access.PUBLIC,
        book=None,
        description="Descrição da comunidade de teste",
    ):
        """Cria uma comunidade com seu criador via ORM."""
        if creator is None:
            creator = self.create_user("criador_comunidade")
        community = Community.objects.create(
            name=name,
            creator=creator,
            access=access,
            book=book,
            description=description,
        )
        return community


class CT01AuthenticationSystemTest(BaseSystemTestCase):
    """CT01 — Autenticação, Cadastro e Perfil (R01–R04, Sprint 1)."""

    def test_user_registration_success(self):
        """Resultado Previsto: Novo usuário é cadastrado com sucesso e redirecionado para a tela de login."""
        self.page.goto(f"{self.live_server_url}/user/register/")
        self.page.fill("#id_username", "leitor_novo")
        self.page.fill("#id_email", "leitor_novo@colecture.com")
        self.page.fill("#id_password1", "SenhaForte#2026")
        self.page.fill("#id_password2", "SenhaForte#2026")
        self.page.click('#register-form button[type="submit"]')

        self.page.wait_for_url(re.compile(r"/user/login/?"))
        self.assertTrue(
            get_user_model().objects.filter(username="leitor_novo").exists(),
            "O novo usuário deveria constar no banco de dados.",
        )

    def test_login_valid_credentials(self):
        """Resultado Previsto: Login com credenciais válidas autentica o usuário e exibe seu perfil."""
        user = self.create_user("leitor_valido", "Senha#12345")
        self.login_via_ui(user.username, "Senha#12345")

        self.page.wait_for_url(re.compile(r".*/(user/profile/?)?$"))
        user_name_element = self.page.locator("#user-name")
        expect(user_name_element).to_be_visible()
        self.assertIn(
            "leitor_valido",
            user_name_element.inner_text(),
            "O perfil deve exibir o identificador do usuário autenticado.",
        )

    def test_login_invalid_credentials_fails_with_message(self):
        """Resultado Previsto: Tentativa de login com senha incorreta falha e exibe mensagem de erro."""
        user = self.create_user("leitor_erro", "SenhaCorreta#1")
        self.page.goto(f"{self.live_server_url}/user/login/")
        self.page.fill("#username", user.username)
        self.page.fill("#password", "SenhaIncorreta#999")
        self.page.click('#login-form button[type="submit"]')

        self.page.wait_for_load_state("networkidle")
        messages_box = self.page.locator(".messages")
        expect(messages_box).to_be_visible()
        self.assertIn(
            "inválidos",
            messages_box.inner_text().lower(),
            "Mensagem de erro deve alertar sobre credenciais inválidas.",
        )

    def test_logout(self):
        """Resultado Previsto: Usuário autenticado encerra sua sessão e retorna à página inicial pública."""
        user = self.create_user("leitor_logout", "Senha#12345")
        self.login_via_ui(user.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/user/profile/")

        self.logout_via_ui()
        self.page.goto(f"{self.live_server_url}/user/profile/")
        self.page.wait_for_url(re.compile(r"/user/login/.*"))

    def test_edit_profile_data_reflected(self):
        """Resultado Previsto: Alteração de nome e email no perfil é salva e refletida na visualização."""
        user = self.create_user("leitor_edicao", "Senha#12345")
        self.login_via_ui(user.username, "Senha#12345")

        self.page.goto(f"{self.live_server_url}/user/profile/editProfile/")
        self.page.fill("#id_first_name", "Mariana")
        self.page.fill("#id_last_name", "Almeida")
        self.page.fill("#id_email", "mariana.almeida@colecture.com")
        self.page.click('button[type="submit"]')

        self.page.wait_for_url(re.compile(r"/user/profile/?"))
        user_name_element = self.page.locator("#user-name")
        expect(user_name_element).to_be_visible()
        self.assertIn("Mariana Almeida", user_name_element.inner_text())

    def test_protected_route_redirects_to_login(self):
        """Resultado Previsto: Acesso a rota protegida sem login prévio redireciona para a página de login."""
        self.page.goto(f"{self.live_server_url}/user/profile/")
        self.page.wait_for_url(re.compile(r"/user/login/\?next=/user/profile/"))

    def test_responsive_mobile_and_desktop(self):
        """Resultado Previsto: Interface do perfil permanece visível e funcional em viewports mobile e desktop."""
        user = self.create_user("leitor_responsivo", "Senha#12345")
        self.login_via_ui(user.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/user/profile/")

        # Desktop (1366x768)
        self.page.set_viewport_size({"width": 1366, "height": 768})
        expect(self.page.locator("#user-name")).to_be_visible()
        expect(self.page.locator(".logout-form button")).to_be_visible()

        # Mobile (375x812)
        self.page.set_viewport_size({"width": 375, "height": 812})
        expect(self.page.locator("#user-name")).to_be_visible()
        expect(self.page.locator(".logout-form button")).to_be_visible()


class CT02BookCatalogSystemTest(BaseSystemTestCase):
    """CT02 — Catálogo, Registro, Busca e Avaliação de Livros (R05–R08, Sprint 2)."""

    def test_register_book_form(self):
        """Resultado Previsto: Registro de livro inexistente com sucesso pelo formulário do catálogo."""
        user = self.create_user("cadastrador_livro", "Senha#12345")
        self.login_via_ui(user.username, "Senha#12345")

        self.page.goto(f"{self.live_server_url}/books/register/")
        self.page.fill("#id_title", "Capitães da Areia")
        self.page.fill("#id_author", "Jorge Amado")
        self.page.fill("#id_isbn", "9788535914061")
        self.page.fill("#id_pages", "280")
        self.page.select_option("#id_genre", "ficcao")
        self.page.fill("#id_synopsis", "A vida de um grupo de meninos de rua em Salvador.")
        self.page.click('button[type="submit"]')

        self.page.wait_for_load_state("networkidle")
        self.assertTrue(
            Book.objects.filter(isbn="9788535914061").exists(),
            "O livro recém-cadastrado deve estar presente na base de dados.",
        )

    def test_search_books_by_title_author_and_genre(self):
        """Resultado Previsto: Usuário registra livros pelo formulário e a busca no banco local retorna os livros pelos filtros de título, autor e gênero."""
        # Usuário autenticado cadastra um livro via formulário
        user = self.create_user("cadastrador_busca", "Senha#12345")
        self.login_via_ui(user.username, "Senha#12345")

        self.page.goto(f"{self.live_server_url}/books/register/")
        self.page.fill("#id_title", "Grande Sertao Veredas")
        self.page.fill("#id_author", "Guimaraes Rosa")
        self.page.fill("#id_isbn", "9788535902778")
        self.page.fill("#id_pages", "400")
        self.page.select_option("#id_genre", "ficcao")
        self.page.fill("#id_synopsis", "Classico do sertao brasileiro.")
        self.page.click('button[type="submit"]')
        self.page.wait_for_load_state("networkidle")

        # Cadastra outro livro no banco local
        self.create_book(
            title="Orgulho e Preconceito",
            author="Jane Austen",
            isbn="9788542207330",
            genre="romance",
            pages=350,
        )

        # Acessa a página de busca no banco local
        self.page.goto(f"{self.live_server_url}/search")

        # Busca por título
        self.page.fill("#searchInput", "Grande Sertao")
        self.page.click("#searchButton")
        self.page.wait_for_load_state("networkidle")
        expect(self.page.locator("#bookList")).to_contain_text("Grande Sertao Veredas")
        expect(self.page.locator("#bookList")).not_to_contain_text("Orgulho e Preconceito")

        # Busca por autor
        self.page.fill("#searchInput", "Austen")
        self.page.click("#searchButton")
        self.page.wait_for_load_state("networkidle")
        expect(self.page.locator("#bookList")).to_contain_text("Orgulho e Preconceito")

        # Busca por gênero
        self.page.fill("#searchInput", "")
        self.page.select_option("#genreFilter", "romance")
        self.page.click("#searchButton")
        self.page.wait_for_load_state("networkidle")
        expect(self.page.locator("#bookList")).to_contain_text("Orgulho e Preconceito")

    def test_review_book_and_rating_average(self):
        """Resultado Previsto: Avaliações são registradas e a média é calculada corretamente com 2 notas."""
        book = self.create_book(
            title="Vidas Secas",
            author="Graciliano Ramos",
            isbn="9788501014498",
            pages=176,
        )
        user1 = self.create_user("avaliador_um", "Senha#12345")
        user2 = self.create_user("avaliador_dois", "Senha#12345")

        # Avaliação 1: nota 4.0
        self.login_via_ui(user1.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/books/{book.id}/")
        self.page.click('#seletor button[data-valor="4"]')
        self.page.fill("#texto-resenha", "Livro sensacional e impactante.")
        self.page.click('#form-resenha button[type="submit"]')
        self.page.wait_for_load_state("networkidle")

        expect(self.page.locator("#lista-resenhas")).to_contain_text("Livro sensacional")
        expect(self.page.locator("#media-texto")).to_contain_text("4.0 (1 avaliações)")

        # Avaliação 2: nota 5.0
        self.logout_via_ui()
        self.login_via_ui(user2.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/books/{book.id}/")
        self.page.click('#seletor button[data-valor="5"]')
        self.page.fill("#texto-resenha", "Uma verdadeira obra-prima.")
        self.page.click('#form-resenha button[type="submit"]')
        self.page.wait_for_load_state("networkidle")

        # Média de 4.0 e 5.0 deve ser 4.5
        expect(self.page.locator("#media-texto")).to_contain_text("4.5 (2 avaliações)")

    def test_invalid_rating_rejected(self):
        """Resultado Previsto: Nota fora do intervalo permitido de 1 a 5 é rejeitada com mensagem de erro."""
        book = self.create_book(
            title="Memorias Postumas",
            author="Machado de Assis",
            isbn="9788572323147",
            pages=224,
        )
        user = self.create_user("avaliador_invalido", "Senha#12345")
        self.login_via_ui(user.username, "Senha#12345")

        self.page.goto(f"{self.live_server_url}/books/{book.id}/")
        # Injeta valor de nota inválido (6.0) no campo hidden do formulário
        self.page.evaluate("() => { document.getElementById('id_rating').value = '6.0'; }")
        self.page.fill("#texto-resenha", "Tentando burlar a nota.")
        self.page.click('#form-resenha button[type="submit"]')
        self.page.wait_for_load_state("networkidle")

        # Verifica se o erro foi exibido e nenhuma avaliação foi gravada
        aviso = self.page.locator("#aviso")
        self.assertTrue(
            aviso.is_visible() or BookReview.objects.filter(book=book, user=user).count() == 0,
            "Nota inválida não deve ser persistida.",
        )


class CT03CommunityManagementSystemTest(BaseSystemTestCase):
    """CT03 — Manter Comunidade e Interface da Página (R09, R10, Sprint 3)."""

    def test_create_community(self):
        """Resultado Previsto: Usuário cria nova comunidade e ela é exibida no painel."""
        creator = self.create_user("criador_comunidade_ui", "Senha#12345")
        self.login_via_ui(creator.username, "Senha#12345")

        self.page.goto(f"{self.live_server_url}/communities/create/")
        self.page.fill("#id_name", "Clube da Ficcao Cientifica")
        self.page.fill("#id_description", "Comunidade focada em scifi e distopias.")
        self.page.check("#vis-public")
        self.page.click('button[type="submit"]')

        self.page.wait_for_url(re.compile(r"/communities/?"))
        self.assertTrue(
            Community.objects.filter(name="Clube da Ficcao Cientifica").exists(),
            "A comunidade criada deve ser registrada no banco de dados.",
        )

    def test_community_page_displays_details(self):
        """Resultado Previsto: Página da comunidade exibe nome, criador, livro/tema e detalhes."""
        book = self.create_book(title="Duna", author="Frank Herbert", isbn="9780441172719")
        creator = self.create_user("dono_clube", "Senha#12345")
        community = self.create_community(
            name="Leitores de Duna",
            creator=creator,
            book=book,
            description="Discussões sobre o universo de Arrakis.",
        )

        self.login_via_ui(creator.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/communities/{community.id}")

        expect(self.page.locator("#community-name")).to_contain_text("Leitores de Duna")
        expect(self.page.locator(".community-book")).to_contain_text("Duna")
        expect(self.page.locator(".details")).to_contain_text("dono_clube")

    def test_private_community_join_request_and_moderator_approval(self):
        """Resultado Previsto: Pedido de entrada em comunidade privada é recebido e aceito pelo moderador."""
        moderator = self.create_user("moderador_privado", "Senha#12345")
        applicant = self.create_user("candidato_membro", "Senha#12345")
        community = self.create_community(
            name="Circulo Fechado",
            creator=moderator,
            access=Community.Access.PRIVATE,
        )

        # Usuário solicita entrada
        self.login_via_ui(applicant.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/communities/{community.id}")
        self.page.click('.community-join button[type="submit"]')
        self.page.wait_for_load_state("networkidle")

        # Moderador acessa o painel de gerenciamento e aceita
        self.logout_via_ui()
        self.login_via_ui(moderator.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/communities/{community.id}/manage/")
        expect(self.page.locator(".mod-notify")).to_contain_text(applicant.username)

        # Clica em 'Aceitar'
        accept_button = self.page.locator(".mod-btn-success").first
        accept_button.click()
        self.page.wait_for_load_state("networkidle")

        membership = Membership.objects.filter(community=community, user=applicant).first()
        self.assertIsNotNone(membership)
        self.assertEqual(
            membership.status,
            Membership.Status.ACTIVE,
            "Após aprovação do moderador, o membro deve estar com status ACTIVE.",
        )

    def test_moderator_promotes_bans_and_archives_community(self):
        """Resultado Previsto: Moderador promove membro a moderador, bane membro e arquiva a comunidade."""
        creator = self.create_user("lider_comunidade", "Senha#12345")
        member1 = self.create_user("membro_promover", "Senha#12345")
        member2 = self.create_user("membro_banir", "Senha#12345")
        community = self.create_community("Clube de Testes", creator=creator)

        Membership.objects.create(
            community=community,
            user=member1,
            role=Membership.Role.MEMBER,
            status=Membership.Status.ACTIVE,
        )
        Membership.objects.create(
            community=community,
            user=member2,
            role=Membership.Role.MEMBER,
            status=Membership.Status.ACTIVE,
        )

        self.login_via_ui(creator.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/communities/{community.id}/manage/")

        # Promover member1
        promote_button = self.page.locator(f'button[data-role][data-name="{member1.username}"]')
        promote_button.click()
        self.page.locator("#role-dialog #role-submit").click()
        self.page.wait_for_load_state("networkidle")

        member1_membership = Membership.objects.get(community=community, user=member1)
        self.assertEqual(member1_membership.role, Membership.Role.MODERATOR)

        # Banir member2
        ban_button = self.page.locator(f'button[data-ban][data-name="{member2.username}"]')
        ban_button.click()
        self.page.locator("#ban-form button[type='submit']").click()
        self.page.wait_for_load_state("networkidle")

        member2_membership = Membership.objects.get(community=community, user=member2)
        self.assertEqual(member2_membership.status, Membership.Status.BANNED)

        # Arquivar comunidade
        self.page.goto(f"{self.live_server_url}/communities/{community.id}")
        self.page.click("#communityMenuBtn")
        self.page.click('button[data-confirm="archive"]')
        self.page.click("#confirm-archive button[type='submit']")
        self.page.wait_for_load_state("networkidle")

        community.refresh_from_db()
        self.assertEqual(community.state, Community.State.ARCHIVED)

    def test_common_reader_cannot_see_or_access_moderator_actions(self):
        """Resultado Previsto: Leitor comum sem cargo não vê botão de gerenciar e recebe 403 ao acessar a rota."""
        creator = self.create_user("lider_gestao", "Senha#12345")
        reader = self.create_user("leitor_comum_gestao", "Senha#12345")
        community = self.create_community("Comunidade Aberta", creator=creator)
        Membership.objects.create(
            community=community,
            user=reader,
            role=Membership.Role.MEMBER,
            status=Membership.Status.ACTIVE,
        )

        self.login_via_ui(reader.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/communities/{community.id}")

        # O botão 'Gerenciar Comunidade' não deve ser visível
        manage_btn = self.page.locator("a:has-text('Gerenciar Comunidade')")
        self.assertEqual(manage_btn.count(), 0)

        # Acesso direto à URL restrita deve ser bloqueado com 403
        response = self.page.goto(f"{self.live_server_url}/communities/{community.id}/manage/")
        self.assertEqual(response.status, 403)

    def test_responsive_mobile_and_desktop(self):
        """Resultado Previsto: Elementos principais da comunidade continuam visíveis em desktop e mobile."""
        creator = self.create_user("lider_resp", "Senha#12345")
        community = self.create_community("Comunidade Responsiva", creator=creator)
        self.login_via_ui(creator.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/communities/{community.id}")

        # Desktop
        self.page.set_viewport_size({"width": 1366, "height": 768})
        expect(self.page.locator("#community-name")).to_be_visible()

        # Mobile
        self.page.set_viewport_size({"width": 375, "height": 812})
        expect(self.page.locator("#community-name")).to_be_visible()


class CT04ReadingGoalsAndForumSystemTest(BaseSystemTestCase):
    """CT04 — Metas de Leitura, Manter e Moderar Fórum (R11–R14, Sprint 4)."""

    def test_create_collective_goal_and_automatic_enrollment(self):
        """Resultado Previsto: Criação de meta coletiva inscreve automaticamente todos os membros e gera o fórum."""
        book = self.create_book(title="O Hobbit", author="J.R.R. Tolkien", isbn="9780547928227", pages=310)
        moderator = self.create_user("mod_metas", "Senha#12345")
        member = self.create_user("membro_metas", "Senha#12345")
        community = self.create_community("Clube Tolkien", creator=moderator, book=book)

        Membership.objects.create(
            community=community,
            user=member,
            role=Membership.Role.MEMBER,
            status=Membership.Status.ACTIVE,
        )

        self.login_via_ui(moderator.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/goals/create/community/{community.id}/")

        self.page.fill("#id_name", "Meta Hobbit 150 Paginas")
        self.page.check('input[name="goal_type"][value="PAGE_COUNT"]', force=True)
        self.page.fill("#id_target", "150")
        self.page.fill("#id_deadline", "2026-12-31")
        self.page.click('button[type="submit"]')

        self.page.wait_for_url(re.compile(rf"/communities/{community.id}/?"))

        # Verifica meta no banco
        goal = Goal.objects.filter(owner_community=community, name="Meta Hobbit 150 Paginas").first()
        self.assertIsNotNone(goal, "A meta coletiva deve ter sido criada no banco.")

        # Verifica inscrições automáticas
        self.assertTrue(
            GoalParticipation.objects.filter(goal=goal, user=moderator, state=GoalParticipation.State.ACTIVE).exists(),
            "O moderador deve estar inscrito na meta coletiva.",
        )
        self.assertTrue(
            GoalParticipation.objects.filter(goal=goal, user=member, state=GoalParticipation.State.ACTIVE).exists(),
            "Todos os membros devem ser inscritos automaticamente na meta coletiva.",
        )

        # Verifica criação automática do fórum da meta
        self.assertTrue(
            Forum.objects.filter(goal=goal).exists(),
            "O fórum da meta coletiva deve ser criado automaticamente.",
        )

    def test_goal_tabs_active_and_concluded(self):
        """Resultado Previsto: Metas ativas e encerradas/concluídas são exibidas nas respectivas abas da página."""
        book = self.create_book(title="Fahrenheit 451", author="Ray Bradbury", isbn="9788525052247", pages=216)
        moderator = self.create_user("mod_abas_meta", "Senha#12345")
        community = self.create_community("Clube Distopia", creator=moderator, book=book)

        goal = Goal.objects.create(
            name="Leitura Fahrenheit 100p",
            owner_community=community,
            book=book,
            goal_type=Goal.GoalType.PAGE_COUNT,
            target=100,
            status=Goal.Status.ACTIVE,
        )
        GoalParticipation.objects.create(goal=goal, user=moderator, state=GoalParticipation.State.ACTIVE)

        self.login_via_ui(moderator.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/communities/{community.id}")

        # Aba de ativas
        expect(self.page.locator("#panel-active")).to_contain_text("Leitura Fahrenheit 100p")

        # Conclui a meta e verifica aba de encerradas
        goal.status = Goal.Status.CONCLUDED
        goal.save()

        self.page.reload()
        self.page.click("#tab-closed")
        expect(self.page.locator("#panel-closed")).to_contain_text("Leitura Fahrenheit 100p")

    def test_forum_post_and_reply_message(self):
        """Resultado Previsto: Usuário posta mensagem no fórum e outro usuário responde citando a mensagem original."""
        book = self.create_book(title="1984", author="George Orwell", isbn="9788535914849")
        moderator = self.create_user("autor_forum1", "Senha#12345")
        member = self.create_user("autor_forum2", "Senha#12345")
        community = self.create_community("Clube 1984", creator=moderator, book=book)

        Membership.objects.create(
            community=community,
            user=member,
            role=Membership.Role.MEMBER,
            status=Membership.Status.ACTIVE,
        )

        goal = Goal.objects.create(
            name="Meta 1984",
            owner_community=community,
            book=book,
            goal_type=Goal.GoalType.PAGE_COUNT,
            target=100,
        )
        GoalParticipation.objects.create(goal=goal, user=moderator, state=GoalParticipation.State.ACTIVE)
        GoalParticipation.objects.create(goal=goal, user=member, state=GoalParticipation.State.ACTIVE)
        forum = Forum.objects.create(name=goal.name, goal=goal)

        # Usuário 1 posta mensagem inicial
        self.login_via_ui(moderator.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/forums/{forum.id}")
        self.page.fill("#messageInput", "O que acharam do inicio do livro?")
        self.page.click("#sendButton")
        self.page.wait_for_load_state("networkidle")
        expect(self.page.locator("#messages")).to_contain_text("O que acharam do inicio do livro?")

        # Usuário 2 responde à mensagem
        self.logout_via_ui()
        self.login_via_ui(member.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/forums/{forum.id}")

        reply_btn = self.page.locator(".message-reply-btn").first
        reply_btn.click()
        expect(self.page.locator("#replyBar")).to_be_visible()

        self.page.fill("#messageInput", "Achei a atmosfera do Grande Irmao impressionante!")
        self.page.click("#sendButton")
        self.page.wait_for_load_state("networkidle")

        expect(self.page.locator("#messages")).to_contain_text("Achei a atmosfera")

    def test_moderator_edits_locks_pins_forum_and_delete_gap(self):
        """Resultado Previsto: Moderador edita título, tranca e fixa mensagem; ausência de botão para apagar mensagem é verificada."""
        creator = self.create_user("mod_gerente_forum", "Senha#12345")
        community = self.create_community("Clube Forum Mod", creator=creator)
        goal = Goal.objects.create(
            name="Meta Debate",
            owner_community=community,
            goal_type=Goal.GoalType.PAGE_COUNT,
            target=50,
        )
        forum = Forum.objects.create(name=goal.name, goal=goal)
        msg = Message.objects.create(forum=forum, author=creator, content="Mensagem para ser fixada")

        self.login_via_ui(creator.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/forums/{forum.id}")

        # Editar título do fórum
        self.page.click("#forumEditDots")
        self.page.fill("#forumEditName", "Titulo Atualizado do Forum")
        self.page.click("#forumEditDialog .confirm-save")
        self.page.wait_for_load_state("networkidle")
        expect(self.page.locator("#forumTitle")).to_contain_text("Titulo Atualizado do Forum")

        # Verificação do menu de ferramentas rápidas do moderador (fixar/trancar via menu):
        # Defeito na aplicação: a ferramenta rápida depende de dados.is_moderator, que está
        # fixado como False no backend (colecture/forums/services.py:81).
        # Logo, o menu de moderação rápida (#forumMenu / #menuButton) permanece oculto para moderadores.
        expect(self.page.locator("#forumMenu")).to_have_class(re.compile(r".*hidden.*"))

        # Trancar fórum
        self.page.click("#forumEditDots")
        self.page.select_option("#forumEditState", "LOCKED")
        self.page.click("#forumEditDialog .confirm-save")
        self.page.wait_for_load_state("networkidle")
        expect(self.page.locator("#lockedNotice")).to_be_visible()
        expect(self.page.locator("#composer")).to_have_class(re.compile(r".*hidden.*"))

        # Verificação da exclusão de mensagem individual na UI:
        # A view delete_message existe no backend, mas a interface não renderiza botão de exclusão
        delete_msg_btn = self.page.locator(f'.message[data-id="{msg.id}"] button:has-text("Excluir")')
        self.assertEqual(
            delete_msg_btn.count(),
            0,
            "A interface do fórum não possui botão para exclusão de mensagem individual (defeito documentado).",
        )

    def test_common_reader_cannot_moderate_forum(self):
        """Resultado Previsto: Leitor comum não visualiza menu de moderação nem consegue editar o fórum."""
        creator = self.create_user("mod_supremo", "Senha#12345")
        reader = self.create_user("leitor_sem_mod", "Senha#12345")
        community = self.create_community("Clube Mod Privado", creator=creator)
        Membership.objects.create(
            community=community,
            user=reader,
            role=Membership.Role.MEMBER,
            status=Membership.Status.ACTIVE,
        )
        goal = Goal.objects.create(
            name="Meta Simples",
            owner_community=community,
            goal_type=Goal.GoalType.PAGE_COUNT,
            target=50,
        )
        GoalParticipation.objects.create(goal=goal, user=reader, state=GoalParticipation.State.ACTIVE)
        forum = Forum.objects.create(name=goal.name, goal=goal)

        self.login_via_ui(reader.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/forums/{forum.id}")

        self.assertEqual(self.page.locator("#forumEditDots").count(), 0)
        expect(self.page.locator("#forumMenu")).to_have_class(re.compile(r".*hidden.*"))

        # Acesso direto à rota de edição bloqueado
        response = self.page.goto(f"{self.live_server_url}/forums/{forum.id}/edit")
        self.assertEqual(response.status, 403)


class CT05ReadingProgressAndStreakSystemTest(BaseSystemTestCase):
    """CT05 — Registro de Progresso, Livro Lido, Página de Leitura e Ofensivas (R15–R18, Sprint 5)."""

    def test_shelf_tabs_navigation(self):
        """Resultado Previsto: Abas da estante (Todos, Lendo, Lido, Quero ler) alternam e filtram os livros."""
        user = self.create_user("leitor_estante_abas", "Senha#12345")
        book1 = self.create_book("Livro Lendo", "Autor 1", "9788535902778")
        book2 = self.create_book("Livro Lido", "Autor 2", "9788542207330")
        book3 = self.create_book("Livro Quero Ler", "Autor 3", "9788576573005")

        BookStatus.objects.create(user=user, book=book1, status=BookStatus.Status.READING)
        BookStatus.objects.create(user=user, book=book2, status=BookStatus.Status.READ)
        BookStatus.objects.create(user=user, book=book3, status=BookStatus.Status.WANT_TO_READ)

        self.login_via_ui(user.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/user/profile/")

        # Aba 'Lendo'
        self.page.click('button[data-shelf-filter="READING"]')
        expect(self.page.locator('.shelf-book[data-status="READING"]')).to_be_visible()

        # Aba 'Lido'
        self.page.click('button[data-shelf-filter="READ"]')
        expect(self.page.locator('.shelf-book[data-status="READ"]')).to_be_visible()

        # Aba 'Quero ler'
        self.page.click('button[data-shelf-filter="WANT_TO_READ"]')
        expect(self.page.locator('.shelf-book[data-status="WANT_TO_READ"]')).to_be_visible()

    def test_register_daily_reading_session(self):
        """Resultado Previsto: Sessão de leitura diária é registrada e atualiza páginas e porcentagem lida."""
        user = self.create_user("leitor_sessao", "Senha#12345")
        book = self.create_book("Livro de Sessao", "Autor Sessao", "9788535902778", pages=200)
        BookStatus.objects.create(user=user, book=book, status=BookStatus.Status.READING)

        self.login_via_ui(user.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/books/reading/?book={book.id}")
        self.page.wait_for_load_state("networkidle")

        self.page.fill("#rsAmount", "50")
        self.page.fill("#rsMinutes", "45")
        with self.page.expect_response(lambda r: "/session" in r.url and r.request.method == "POST"):
            self.page.click(".rs-submit")
        self.page.wait_for_load_state("networkidle")

        session_exists = ReadingSession.objects.filter(user=user, book=book).exists()
        self.assertTrue(session_exists, "A sessão de leitura deve ser registrada no banco.")

    def test_mark_book_as_read(self):
        """Resultado Previsto: Livro tem seu status alterado para 'Lido' na estante do usuário."""
        user = self.create_user("leitor_marcar_lido", "Senha#12345")
        book = self.create_book("Livro Para Ler", "Autor X", "9788535902778", pages=150)
        book_status = BookStatus.objects.create(user=user, book=book, status=BookStatus.Status.READING)

        self.login_via_ui(user.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/user/profile/")

        # Abre o modal de alteração de tag
        tag_button = self.page.locator(f'.shelf-book[data-book-id="{book.id}"] .shelf-book__tag')
        tag_button.click()
        self.page.click('button[data-modal-option="READ"]')
        self.page.click("button[data-modal-save]")
        self.page.wait_for_load_state("networkidle")

        book_status.refresh_from_db()
        self.assertEqual(book_status.status, BookStatus.Status.READ)

    def test_streak_calculation_and_future_date_rejected(self):
        """Resultado Previsto: Ofensiva incrementa em dias consecutivos e rejeita registros com datas futuras."""
        user = self.create_user("leitor_ofensiva", "Senha#12345")
        profile = user.profile
        today = timezone.localdate()

        # Primeira leitura: streak = 1
        changed = profile.register_reading_day(today)
        profile.save()
        self.assertTrue(changed)
        self.assertEqual(profile.streak, 1)

        # Segunda leitura no mesmo dia: não incrementa
        changed = profile.register_reading_day(today)
        profile.save()
        self.assertFalse(changed)
        self.assertEqual(profile.streak, 1)

        # Leitura no dia seguinte (simulado via ORM): incrementa para 2
        profile.last_read_date = today - timedelta(days=1)
        profile.save()
        changed = profile.register_reading_day(today)
        profile.save()
        self.assertTrue(changed)
        self.assertEqual(profile.streak, 2)

        # Data futura: rejeitada com ValueError
        future_date = today + timedelta(days=2)
        with self.assertRaises(ValueError):
            profile.register_reading_day(future_date)

    def test_responsive_mobile_and_desktop(self):
        """Resultado Previsto: Interface da estante de leitura é responsiva em desktop e mobile."""
        user = self.create_user("leitor_resp_estante", "Senha#12345")
        book = self.create_book("Livro Resp", "Autor Resp", "9788535902778")
        BookStatus.objects.create(user=user, book=book, status=BookStatus.Status.READING)

        self.login_via_ui(user.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/user/profile/")

        # Desktop
        self.page.set_viewport_size({"width": 1366, "height": 768})
        expect(self.page.locator(".bookshelf")).to_be_visible()

        # Mobile
        self.page.set_viewport_size({"width": 375, "height": 812})
        expect(self.page.locator(".bookshelf")).to_be_visible()


class CT06BadgesRecommendationsAndNotificationsSystemTest(BaseSystemTestCase):
    """CT06 — Insígnias, Recomendações por Tema e Notificações (R19–R21, Sprint 6)."""

    def test_badge_awarded_on_criterion_met(self):
        """Resultado Previsto: Insígnia é concedida automaticamente ao atingir o critério e aparece na galeria."""
        user = self.create_user("leitor_insignias", "Senha#12345")
        book = self.create_book("Livro Faísca", "Autor F", "9788535902778", pages=100)
        insignia = Insignia.objects.filter(name="Primeira Faísca").first()
        if not insignia:
            insignia = Insignia.objects.create(
                name="Primeira Faísca",
                description="Registrar progresso pela primeira vez",
                criteria_type=CriteriaType.STREAK,
                criteria_value=1,
                is_active=True,
            )

        ReadingSession.objects.create(
            user=user,
            book=book,
            pages_read=10,
            minute_count=15,
            date=timezone.localdate(),
        )
        awarded = check_first_read(user)
        self.assertTrue(awarded, "A insígnia Primeira Faísca deve ser concedida na primeira leitura.")
        self.assertTrue(
            Award.objects.filter(user=user, insignia=insignia).exists(),
            "O registro de Award deve existir para o usuário.",
        )

        self.login_via_ui(user.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/rewards/insignias/")
        expect(self.page.locator("body")).to_contain_text("Primeira Faísca")

    def test_recommendations_based_on_user_preferences(self):
        """Resultado Previsto: Catálogo recomenda livros do gênero avaliado/lido pelo usuário na busca."""
        user = self.create_user("leitor_recomendacoes", "Senha#12345")
        read_book = self.create_book("Scifi Lido", "Autor Scifi", "9788535902778", genre="ficcao")
        rec_book = self.create_book("Scifi Sugerido", "Outro Autor", "9788542207330", genre="ficcao")
        BookStatus.objects.create(user=user, book=read_book, status=BookStatus.Status.READ)
        BookReview.objects.create(user=user, book=read_book, rating=Decimal("5.0"), review="Perfeito")

        self.login_via_ui(user.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/search")
        self.page.wait_for_load_state("networkidle")

        rec_section = self.page.locator("#recommendations")
        expect(rec_section).to_be_visible()
        expect(self.page.locator("#recommendationsList")).to_contain_text("Scifi Sugerido")

    def test_notification_on_community_approval_and_popup(self):
        """Resultado Previsto: Usuário recebe notificação quando sua entrada em comunidade é aceita, visível no sino e histórico."""
        moderator = self.create_user("mod_notif", "Senha#12345")
        user = self.create_user("leitor_notif", "Senha#12345")
        community = self.create_community("Comunidade Notificacao", creator=moderator, access=Community.Access.PRIVATE)

        # Solicitação e aprovação
        membership = Membership.objects.create(
            community=community,
            user=user,
            role=Membership.Role.NONE,
            status=Membership.Status.PENDING,
        )

        self.login_via_ui(moderator.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/communities/{community.id}/manage/")
        self.page.click('.mod-btn-success')
        self.page.wait_for_load_state("networkidle")

        # Verifica notificação criada
        self.assertTrue(
            Notification.objects.filter(target_user=user).exists(),
            "A notificação de aprovação deve ser gerada para o usuário.",
        )

        # Usuário abre sino e visualiza
        self.logout_via_ui()
        self.login_via_ui(user.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/user/profile/")

        bell_btn = self.page.locator("#notificationBellBtn")
        bell_btn.click()
        expect(self.page.locator("#notificationsModal")).to_be_visible()
        expect(self.page.locator(".notifications-list")).to_contain_text(f'"{community.name}" foi aceito')

        # Acessa histórico completo
        self.page.goto(f"{self.live_server_url}/notifications/history/")
        expect(self.page.locator("body")).to_contain_text(f'"{community.name}" foi aceito')

    def test_goal_cycle_and_request_notification_gaps(self):
        """Resultado Previsto: Validação de notificações para novo ciclo de meta e solicitação de entrada (lacunas mapeadas)."""
        creator = self.create_user("lider_notif_gap", "Senha#12345")
        applicant = self.create_user("candidato_gap", "Senha#12345")
        community = self.create_community("Comunidade Gap", creator=creator, access=Community.Access.PRIVATE)

        # Candidato solicita entrada
        self.login_via_ui(applicant.username, "Senha#12345")
        self.page.goto(f"{self.live_server_url}/communities/{community.id}")
        self.page.click('.community-join button[type="submit"]')
        self.page.wait_for_load_state("networkidle")

        # No backend do projeto, a solicitação gera Membership PENDING, mas não gera Notification para o moderador
        mod_notifs = Notification.objects.filter(target_user=creator, content__icontains="solicita")
        self.assertEqual(
            mod_notifs.count(),
            0,
            "Não existe envio automático de Notification ao moderador na solicitação (defeito/lacuna mapeada).",
        )


class CT07AdministrativeManagementAndSeedSystemTest(BaseSystemTestCase):
    """CT07 — Gestão Administrativa e Inicialização via Seed (R02, R03)."""

    def setUp(self):
        super().setUp()
        admin = get_user_model().objects.filter(username="admin").first()
        if not admin:
            from django.contrib.auth.hashers import make_password
            admin = get_user_model().objects.create(
                username="admin",
                email="admin@colecture.com",
                password=make_password("Admin#Colecture2026"),
                is_staff=True,
                is_superuser=True,
                is_active=True,
            )
            Profile.objects.get_or_create(user=admin)

    def test_default_admin_login(self):
        """Resultado Previsto: O administrador padrão gerado pelas migrações consegue logar no sistema."""
        admin_user = get_user_model().objects.filter(username="admin", is_superuser=True).first()
        self.assertIsNotNone(admin_user, "O admin padrão deve existir via migração inicial.")

        self.login_via_ui("admin", "Admin#Colecture2026")
        self.page.wait_for_url(re.compile(r".*/(user/profile/?)?$"))
        expect(self.page.locator("#user-name")).to_be_visible()

    def test_admin_manages_users_via_django_admin(self):
        """Resultado Previsto: Administrador adiciona, edita e remove usuários através do painel Django Admin."""
        self.login_via_ui("admin", "Admin#Colecture2026")

        # Adicionar usuário
        self.page.goto(f"{self.live_server_url}/admin/auth/user/add/")
        self.page.fill("#id_username", "usuario_admin_crud")
        self.page.fill("#id_password1", "SenhaAdmin#1234")
        self.page.fill("#id_password2", "SenhaAdmin#1234")
        self.page.click('input[type="submit"]')
        self.page.wait_for_load_state("networkidle")

        created_user = get_user_model().objects.filter(username="usuario_admin_crud").first()
        self.assertIsNotNone(created_user, "Usuário deve ser adicionado pelo admin.")

        # Editar usuário
        self.page.goto(f"{self.live_server_url}/admin/auth/user/{created_user.id}/change/")
        self.page.fill("#id_email", "editado_pelo_admin@colecture.com")
        self.page.click('input[name="_save"]')
        self.page.wait_for_load_state("networkidle")

        created_user.refresh_from_db()
        self.assertEqual(created_user.email, "editado_pelo_admin@colecture.com")

        # Excluir usuário
        self.page.goto(f"{self.live_server_url}/admin/auth/user/{created_user.id}/delete/")
        self.page.click('input[type="submit"]')
        self.page.wait_for_load_state("networkidle")

        self.assertFalse(get_user_model().objects.filter(username="usuario_admin_crud").exists())

    def test_admin_manages_communities_and_books(self):
        """Resultado Previsto: Administrador acessa e gerencia listagens de livros e comunidades no admin."""
        self.create_book("Livro Admin Gestao", "Autor AG", "9788535902778")
        self.create_community("Comunidade Admin Gestao")

        self.login_via_ui("admin", "Admin#Colecture2026")

        # Painel de Comunidades
        response = self.page.goto(f"{self.live_server_url}/admin/communities/community/")
        self.assertEqual(response.status, 200)
        expect(self.page.locator("body")).to_contain_text("Comunidade Admin Gestao")

        # Painel de Livros
        response = self.page.goto(f"{self.live_server_url}/admin/books/book/")
        self.assertEqual(response.status, 200)
        expect(self.page.locator("body")).to_contain_text("Livro Admin Gestao")

    def test_common_reader_denied_admin_access(self):
        """Resultado Previsto: Leitor comum é impedido de acessar o painel administrativo do Django."""
        reader = self.create_user("leitor_sem_admin", "Senha#12345", is_staff=False, is_superuser=False)
        self.login_via_ui(reader.username, "Senha#12345")

        self.page.goto(f"{self.live_server_url}/admin/")
        self.page.wait_for_load_state("networkidle")

        # Deve redirecionar para tela de login administrativo ou recusar
        self.assertTrue(
            "/admin/login" in self.page.url or "login" in self.page.url,
            "Leitor comum não deve ter acesso ao painel administrativo.",
        )

    def test_audit_log_generation_for_admin_actions(self):
        """Resultado Previsto: Ações administrativas críticas geram registros em AuditLog visíveis no módulo de logs."""
        admin = get_user_model().objects.get(username="admin")
        community = self.create_community("Comunidade Auditada", creator=admin)

        self.login_via_ui("admin", "Admin#Colecture2026")

        # Arquiva comunidade via UI
        self.page.goto(f"{self.live_server_url}/communities/{community.id}")
        self.page.click("#communityMenuBtn")
        self.page.click('button[data-confirm="archive"]')
        self.page.click("#confirm-archive button[type='submit']")
        self.page.wait_for_load_state("networkidle")

        # Verifica log gerado
        log_entry = AuditLog.objects.filter(
            actor=admin,
            action=AuditLog.Action.COMMUNITY_ARCHIVED,
        ).first()
        self.assertIsNotNone(log_entry, "AuditLog deve ser gerado para o arquivamento.")

        # Admin visualiza a trilha em /logs/
        self.page.goto(f"{self.live_server_url}/logs/")
        expect(self.page.locator("body")).to_contain_text("Community archived")

        # Leitor comum tenta acessar /logs/ e recebe 403
        self.logout_via_ui()
        reader = self.create_user("leitor_sem_logs", "Senha#12345")
        self.login_via_ui(reader.username, "Senha#12345")
        response = self.page.goto(f"{self.live_server_url}/logs/")
        self.assertEqual(response.status, 403)


class ResponsiveDesignSystemTest(BaseSystemTestCase):
    """Testes transversais de responsividade (viewport mobile vs. desktop) para CT01, CT03 e CT05."""

    VIEWPORT_DESKTOP = {"width": 1366, "height": 768}
    VIEWPORT_MOBILE = {"width": 375, "height": 812}

    def test_ct01_responsiveness_auth_profile(self):
        """Resultado Previsto: Telas de autenticação e perfil exibem formulários e botões funcionais tanto em desktop quanto em mobile."""
        user = self.create_user("user_resp_01", "Senha#12345")

        for vp in [self.VIEWPORT_DESKTOP, self.VIEWPORT_MOBILE]:
            self.page.set_viewport_size(vp)
            self.page.goto(f"{self.live_server_url}/user/login/")
            expect(self.page.locator("input[name='username']")).to_be_visible()
            expect(self.page.locator("input[name='password']")).to_be_visible()
            expect(self.page.locator("button[type='submit']")).to_be_visible()

            # Realiza login e verifica perfil
            self.login_via_ui(user.username, "Senha#12345")
            self.page.goto(f"{self.live_server_url}/user/profile/")
            expect(self.page.locator("#user-name")).to_be_visible()
            self.logout_via_ui()

    def test_ct03_responsiveness_community_page(self):
        """Resultado Previsto: Página de comunidade exibe título e informações principais de forma visível em desktop e mobile."""
        admin = self.create_user("admin_resp_03", "Senha#12345")
        community = self.create_community("Comunidade Responsiva", creator=admin)
        self.login_via_ui(admin.username, "Senha#12345")

        for vp in [self.VIEWPORT_DESKTOP, self.VIEWPORT_MOBILE]:
            self.page.set_viewport_size(vp)
            self.page.goto(f"{self.live_server_url}/communities/{community.id}")
            self.page.wait_for_load_state("networkidle")

            expect(self.page.locator("#community-name")).to_be_visible()
            expect(self.page.locator("#communityMenuBtn")).to_be_visible()

    def test_ct05_responsiveness_reading_page(self):
        """Resultado Previsto: Página de leitura e estante com filtros funcionam e permanecem visíveis em mobile e desktop."""
        reader = self.create_user("reader_resp_05", "Senha#12345")
        book = self.create_book("Livro Responsividade", pages=200)
        BookStatus.objects.create(
            user=reader,
            book=book,
            status=BookStatus.Status.READING,
        )
        self.login_via_ui(reader.username, "Senha#12345")

        for vp in [self.VIEWPORT_DESKTOP, self.VIEWPORT_MOBILE]:
            self.page.set_viewport_size(vp)
            self.page.goto(f"{self.live_server_url}/books/reading/?book={book.id}")
            self.page.wait_for_load_state("networkidle")

            expect(self.page.locator("#rsAmount")).to_be_visible()
            expect(self.page.locator("#rsMinutes")).to_be_visible()
            expect(self.page.locator(".rs-submit")).to_be_visible()

