from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class SidebarTests(TestCase):
    """Páginas que usam o sidebar.html: a sidebar aparece e a estrutura HTML é válida."""

    def setUp(self):
        user = get_user_model().objects.create_user(username="Leitor", password="senha123456")
        self.client.force_login(user)

    def test_sidebar_e_um_unico_main(self):
        # O sidebar.html já abre um <main>. Um segundo <main> dentro dele é HTML inválido
        # e já quebrou a busca (o JS pegava o <main> de fora, sem o data-search-url).
        for name in ("accounts:profile", "accounts:editProfile", "main:search", "books:register_book"):
            with self.subTest(pagina=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'class="rail"')
                self.assertContains(response, "<main", count=1)

    def test_busca_expoe_url_da_api(self):
        response = self.client.get(reverse("main:search"))
        self.assertContains(response, f'data-search-url="{reverse("books:search")}"')

    def test_perfil_fica_ativo_na_edicao_de_perfil(self):
        response = self.client.get(reverse("accounts:editProfile"))
        self.assertContains(response, 'class="nav-item active"', count=1)


class ErrorPagesTests(TestCase):
    """Página de erro 404 e 403 no padrão visual do projeto."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(username="LeitorComum", password="senha123456")
        self.client.force_login(self.user)

    def test_invalid_url_renders_custom_404_page(self):
        response = self.client.get("/url-que-nao-existe-no-sistema/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Página não encontrada", status_code=404)
        self.assertContains(response, "Voltar para a pesquisa", status_code=404)
        self.assertContains(response, "mascote.png", status_code=404)
        self.assertContains(response, "error.css", status_code=404)
        self.assertContains(response, "<main", count=1, status_code=404)

    def test_forbidden_url_renders_custom_error_page_with_403(self):
        # Usuário leitor comum não tem permissão para acessar /logs/
        response = self.client.get(reverse("logs:log_list"))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Página não encontrada", status_code=403)
        self.assertContains(response, "Voltar para a pesquisa", status_code=403)
        self.assertContains(response, "mascote.png", status_code=403)
        self.assertContains(response, "error.css", status_code=403)
        self.assertContains(response, "<main", count=1, status_code=403)

