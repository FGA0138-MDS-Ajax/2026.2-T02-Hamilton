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
