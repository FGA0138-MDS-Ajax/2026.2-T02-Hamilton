import os
import importlib
from django.apps import apps;
from django.test import TestCase, Client
from django.urls import reverse;
from django.contrib.auth import get_user_model;
from .models import Profile;
"""
CONSIDERAÇÕES IMPORTANTES:
1. A base de dados é limpa após cada caso
de teste (a cada método).

2. Para rodar os testes, utilize o comando
"python manage.py test" no terminal.

"""

# Create your tests here.
class CT01(TestCase):
    def setUp(self):
        self.client = Client();

    def test_criar_conta_valida(self):

        # pega o url da view de registro
        url = reverse("accounts:register");

        # informações que o usuário falso irá enviar
        new_account_data = {
            'username':'NewAccount',
            'email':'newacc@gmail.com',
            'password1':'senha123456',
            'password2':'senha123456',
        }

        # resposta do servidor
        response = self.client.post(url, data=new_account_data);

        # verifica se o servidor aceitou o POST corretamente.
        self.assertEqual(response.status_code, 302);

        # verifica se o usuário existe na base de dados
        newUser = get_user_model().objects.filter(username=new_account_data['username']);
        self.assertTrue(newUser.exists());

    def test_criar_conta_invalida(self):
        # pega o url da view de registro
        url = reverse("accounts:register");

        # informações que o usuário falso irá enviar
        new_account_data = {
            'username':'NewAccount',
            # 'email':'newacc@gmail.com', # faltou o email.
            'password1':'senha123456',
            'password2':'senha123456',
        }

        # resposta do servidor
        response = self.client.post(url, data=new_account_data);

        # verifica se o servidor não aceitou o POST corretamente.
        self.assertNotEqual(response.status_code, 302);

        # verifica se o usuário NÃO existe na base de dados
        newUser = get_user_model().objects.filter(username=new_account_data['username']);
        self.assertFalse(newUser.exists());

    def test_realizar_login_valido(self):
        url = reverse("accounts:login");

        # cria o usuário (pois a base de dados é limpa após cada teste)
        get_user_model().objects.create_user(username='NewAccount', password='senha123456');

        response = self.client.post(url, data={
            'username':'NewAccount',
            'password':'senha123456'
        });

        self.assertEqual(response.status_code, 302);

    def test_realizar_login_invalido(self):
        url = reverse("accounts:login");

        # cria o usuário (pois a base de dados é limpa após cada teste)
        get_user_model().objects.create_user(username='NewAccount', password='senha123456');

        response = self.client.post(url, data={
            'username':'NewAccount',
            'password':'senha' # senha errada
        });

        self.assertNotEqual(response.status_code, 302);

    def test_realizar_logout(self):

        # cria um usuário falso (banco de dados estava vazio)
        user = get_user_model().objects.create_user(username='NewAccount', password='senha123456');

        # força um login do cliente com o usuário criado
        self.client.force_login(user);

        url = reverse("accounts:logout");

        response = self.client.post(url); # faz o logout com POST

        self.assertEqual(response.status_code, 302);

        """
        verifica se o cliente realmente está bloqueado de acessar
        páginas que necessitam de login, tais como a página de 
        edição de perfil. Ou seja, o logout foi bem sucedido.
        """
        profile_url = reverse("accounts:editProfile");
        access_profile = self.client.get(profile_url);
        self.assertNotEqual(access_profile.status_code, 200);

    def test_editar_informacoes_validas(self):
        
        url = reverse("accounts:editProfile");

        user = get_user_model().objects.create_user(
            username="NewAccount",
            password="senha123456",
            first_name="Linus",
            last_name="Torvalds",
            email="newacc@gmail.com"
        );

        # login necessário para acessar a edição de perfil
        self.client.force_login(user);

        response = self.client.post(url, {
            'first_name':'Bill',
            'last_name':'Gates',
            'email':'newacc@gmail.com'
        });

        self.assertEqual(response.status_code, 302);

        # verificando alterações e conservações
        user.refresh_from_db(); # atualiza o objeto User com os dados do banco.
        self.assertEqual(user.first_name, "Bill"); # primeiro nome mudou?
        self.assertEqual(user.last_name, "Gates"); # segundo nome mudou?
        self.assertEqual(user.email, "newacc@gmail.com"); # terceiro nome NÃO mudou?

    def test_editar_informacoes_invalidas(self):

        url = reverse("accounts:editProfile");

        user = get_user_model().objects.create_user(
            username="NewAccount",
            password="senha123456",
            first_name="Linus",
            last_name="Torvalds",
            email="newacc@gmail.com"
        );

        """
        postando ANTES de fazer o login (proibido)
        """
        response = self.client.post(url, {
            'first_name':'Bill',
            'last_name':'Gates',
            'email':'newacc@gmail.com'
        });
        self.assertEqual(response.status_code, 302); # o usuário é redirecionado para login.
        user.refresh_from_db();
        self.assertEqual(user.first_name, "Linus"); # os dados não foram alterados

        """
        postando DEPOIS de fazer o login
        MAS com informações inválidas
        """
        self.client.force_login(user);
        response = self.client.post(url, {
            'first_name':'',
            'last_name':'',
            'email':'newacc@gmail.com'
        });
        self.assertEqual(response.status_code, 302);
        user.refresh_from_db(); # sem isso o assert abaixo olharia o objeto antigo da memória
        self.assertEqual(user.first_name, "Linus");
        self.assertEqual(user.last_name, "Torvalds");

    def test_editar_com_nomes_em_branco_mantem_valores(self):
        # a página diz para deixar os nomes em branco se não for alterá-los
        user = get_user_model().objects.create_user(
            username="NewAccount",
            password="senha123456",
            first_name="Linus",
            last_name="Torvalds",
            email="newacc@gmail.com"
        );
        self.client.force_login(user);

        response = self.client.post(reverse("accounts:editProfile"), {
            'first_name':'',
            'last_name':'',
            'email':'novo@gmail.com'
        });

        self.assertEqual(response.status_code, 302);
        user.refresh_from_db();
        self.assertEqual(user.first_name, "Linus"); # nomes conservados
        self.assertEqual(user.last_name, "Torvalds");
        self.assertEqual(user.email, "novo@gmail.com"); # e-mail alterado normalmente

    def test_perfil_carrega_dados_do_usuario(self):
        user = get_user_model().objects.create_user(
            username="NewAccount",
            password="senha123456",
            first_name="Linus",
            last_name="Torvalds",
            email="newacc@gmail.com"
        );
        self.client.force_login(user);

        response = self.client.get(reverse("accounts:profile"));

        self.assertEqual(response.status_code, 200);
        self.assertContains(response, "Linus Torvalds");
        self.assertContains(response, "@NewAccount");
        self.assertContains(response, "newacc@gmail.com");

    def test_edicao_vem_preenchida_com_dados_atuais(self):
        user = get_user_model().objects.create_user(
            username="NewAccount",
            password="senha123456",
            first_name="Linus",
            last_name="Torvalds",
            email="newacc@gmail.com"
        );
        self.client.force_login(user);

        response = self.client.get(reverse("accounts:editProfile"));

        self.assertEqual(response.status_code, 200);
        self.assertContains(response, 'value="Linus"');
        self.assertContains(response, 'value="Torvalds"');
        self.assertContains(response, 'value="newacc@gmail.com"');

    def test_sidebar_presente_nas_paginas_de_perfil(self):
        user = get_user_model().objects.create_user(username="NewAccount", password="senha123456");
        self.client.force_login(user);

        for name in ("accounts:profile", "accounts:editProfile"):
            response = self.client.get(reverse(name));
            self.assertContains(response, 'class="rail"');
            self.assertContains(response, reverse("main:search"));
            self.assertContains(response, reverse("books:register_book"));

class CT07(TestCase):
    """
    CT07 - Gestão Administrativa e Inicialização via Seed (R02, R03)
 
    O admin é criado pela migration accounts/0002_createDefaultAdmin.
    O TestCase roda as migrations ao montar o banco de testes, então
    o admin já existe no início de cada método. As ações de gerenciar
    usuários (R02) são feitas pelo painel administrativo do Django (/admin/).
    """
 
    def setUp(self):
        self.client = Client();
        self.User = get_user_model();
 
        # mesmos valores padrão da migration (podem ser trocados por variáveis de ambiente)
        self.admin_username = os.environ.get("COLECTURE_ADMIN_USERNAME", "admin");
        self.admin_password = os.environ.get("COLECTURE_ADMIN_PASSWORD", "Admin#Colecture2026");
 
        self.admin = self.User.objects.get(username=self.admin_username);
 
    def _cria_leitor(self, username="Leitor"):
        leitor = self.User.objects.create_user(
            username=username,
            password="senha123456",
            first_name="Linus",
            last_name="Torvalds",
            email=f"{username.lower()}@gmail.com"
        );
        Profile.objects.create(user=leitor);
        return leitor;
 
    # ---------- R03: admin inicial via seed ----------
 
    def test_admin_criado_pela_seed(self):
        self.assertTrue(self.admin.is_superuser);
        self.assertTrue(self.admin.is_staff);
        self.assertTrue(self.admin.is_active);
 
        # o banco inicia vazio: o admin é o único usuário
        self.assertEqual(self.User.objects.count(), 1);
 
    def test_admin_possui_profile(self):
        self.assertTrue(Profile.objects.filter(user=self.admin).exists());
 
    def test_seed_nao_duplica_admin(self):
        # roda a função da migration de novo (como um segundo "migrate")
        migration = importlib.import_module("accounts.migrations.0002_createDefaultAdmin");
        migration.createDefaultAdmin(apps, None);
 
        total = self.User.objects.filter(username=self.admin_username).count();
        self.assertEqual(total, 1);
        self.assertEqual(Profile.objects.filter(user=self.admin).count(), 1);
 
    def test_admin_login_credenciais_padrao(self):
        url = reverse("accounts:login");
 
        response = self.client.post(url, data={
            'username': self.admin_username,
            'password': self.admin_password
        });
 
        self.assertEqual(response.status_code, 302);
 
    def test_admin_login_senha_errada(self):
        url = reverse("accounts:login");
 
        response = self.client.post(url, data={
            'username': self.admin_username,
            'password': 'senhaerrada'
        });
 
        self.assertNotEqual(response.status_code, 302);
 
    # ---------- R02: admin gerencia usuários (painel /admin/) ----------
 
    def test_admin_acessa_painel_e_lista_usuarios(self):
        self.client.force_login(self.admin);
 
        response = self.client.get(reverse("admin:auth_user_changelist"));
 
        self.assertEqual(response.status_code, 200);
 
    def test_admin_adicionar_usuario(self):
        self.client.force_login(self.admin);
 
        url = reverse("admin:auth_user_add");
 
        response = self.client.post(url, {
            'username': 'NovoLeitor',
            'usable_password': 'true',
            'password1': 'senha123456',
            'password2': 'senha123456',
        });
 
        self.assertEqual(response.status_code, 302);
        self.assertTrue(self.User.objects.filter(username='NovoLeitor').exists());
 
    def test_admin_editar_usuario(self):
        leitor = self._cria_leitor();
        self.client.force_login(self.admin);
 
        url = reverse("admin:auth_user_change", args=[leitor.pk]);
 
        response = self.client.post(url, {
            'username': leitor.username,
            'first_name': 'Bill',
            'last_name': 'Gates',
            'email': 'leitor@gmail.com',
            'is_active': 'on',
            'date_joined_0': '2026-01-01',
            'date_joined_1': '00:00:00',
        });
 
        self.assertEqual(response.status_code, 302);
 
        leitor.refresh_from_db();
        self.assertEqual(leitor.first_name, "Bill");
        self.assertEqual(leitor.last_name, "Gates");
        self.assertEqual(leitor.email, "leitor@gmail.com"); # não mudou
 
    def test_admin_excluir_usuario(self):
        leitor = self._cria_leitor();
        self.client.force_login(self.admin);
 
        url = reverse("admin:auth_user_delete", args=[leitor.pk]);
 
        response = self.client.post(url, {'post': 'yes'}); # confirma a exclusão
 
        self.assertEqual(response.status_code, 302);
        self.assertFalse(self.User.objects.filter(pk=leitor.pk).exists());
        self.assertFalse(Profile.objects.filter(user_id=leitor.pk).exists()); # Profile removido em cascata
 
    # ---------- restrição de acesso ----------
 
    def test_leitor_nao_acessa_painel_admin(self):
        leitor = self._cria_leitor();
        alvo = self._cria_leitor("Alvo");
        self.client.force_login(leitor);
 
        # não acessa o painel
        response = self.client.get(reverse("admin:index"));
        self.assertNotEqual(response.status_code, 200);
 
        # não consegue excluir outro usuário
        response = self.client.post(reverse("admin:auth_user_delete", args=[alvo.pk]), {'post': 'yes'});
        self.assertNotEqual(response.status_code, 200);
        self.assertTrue(self.User.objects.filter(pk=alvo.pk).exists());
 
    def test_anonimo_nao_acessa_painel_admin(self):
        alvo = self._cria_leitor("Alvo");
 
        response = self.client.post(reverse("admin:auth_user_delete", args=[alvo.pk]), {'post': 'yes'});
 
        self.assertEqual(response.status_code, 302); # redirecionado para o login do admin
        self.assertTrue(self.User.objects.filter(pk=alvo.pk).exists());

# Estante do perfil: filtro, cards, marcar como lido e acesso ao registro de leitura
class CTEstantePerfil(TestCase):
    def setUp(self):
        from books.models import Book, BookStatus
        self.BookStatus = BookStatus
        self.user = get_user_model().objects.create_user(username="Leitora", password="senha123456")
        self.outro = get_user_model().objects.create_user(username="Outro", password="senha123456")
        self.client.force_login(self.user)

        self.lendo = Book.objects.create(isbn="111", title="Livro Lendo", author="Autora A", pages=200)
        self.quero = Book.objects.create(isbn="222", title="Livro Quero", author="Autora B", pages=150)
        self.lido = Book.objects.create(isbn="333", title="Livro Lido", author="Autora C", pages=100)

        BookStatus.objects.create(user=self.user, book=self.lendo,
                                  status=BookStatus.Status.READING, reading_progress="0.250")
        BookStatus.objects.create(user=self.user, book=self.quero,
                                  status=BookStatus.Status.WANT_TO_READ)
        BookStatus.objects.create(user=self.user, book=self.lido,
                                  status=BookStatus.Status.READ, reading_progress="1.000")

    def test_estante_lista_livros_filtro_e_contadores(self):
        response = self.client.get(reverse("accounts:profile"))

        self.assertContains(response, "Livro Lendo")
        self.assertContains(response, "Livro Quero")
        self.assertContains(response, "Livro Lido")
        for value in ("ALL", "READ", "READING", "WANT_TO_READ"):
            self.assertContains(response, f'data-shelf-filter="{value}"')
        filtros = {f["value"]: f["count"] for f in response.context["shelf_filters"]}
        self.assertEqual(filtros, {"ALL": 3, "READ": 1, "READING": 1, "WANT_TO_READ": 1})

    def test_progresso_aparece_so_em_lendo_e_sem_botao_marcar_lido(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertContains(response, "50/200 pág. · 25%")
        self.assertContains(response, "data-shelf-progress", count=1)
        self.assertNotContains(response, "data-mark-read")  # sem botão "Marcar como lido" no card

    def test_estante_vazia_mantem_texto_padrao(self):
        self.BookStatus.objects.filter(user=self.user).delete()
        response = self.client.get(reverse("accounts:profile"))
        self.assertContains(response, "Você ainda não registrou nenhum livro.")
        self.assertNotContains(response, "data-shelf-grid")

    def test_clique_no_livro_leva_ao_registro_de_progresso_e_popup_de_tag(self):
        response = self.client.get(reverse("accounts:profile"))
        # sem o botão "Registrar leitura" no cabeçalho; o clique no livro usa esta URL
        self.assertNotContains(response, "bookshelf-register")
        self.assertContains(response, f'data-progress-url="{reverse("books:register_reading_session")}"')
        self.assertContains(response, f'data-shelf-url="{reverse("books:manage_bookshelf")}"')
        self.assertContains(response, "data-status-modal")
        self.assertContains(response, "data-change-status", count=3)
        self.assertContains(response, 'class="rail"')

    def test_marcar_como_lido_salva_data_e_progresso(self):
        from decimal import Decimal
        from django.utils import timezone

        for book in (self.lendo, self.quero):
            response = self.client.post(reverse("books:mark_book_as_read", args=[book.id]))
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["success"])

            status = self.BookStatus.objects.get(user=self.user, book=book)
            self.assertEqual(status.status, self.BookStatus.Status.READ)
            self.assertEqual(status.finished_at, timezone.localdate())
            self.assertEqual(status.reading_progress, Decimal("1.000"))

        filtros = {f["value"]: f["count"]
                   for f in self.client.get(reverse("accounts:profile")).context["shelf_filters"]}
        self.assertEqual(filtros["READ"], 3)
        self.assertEqual(filtros["READING"], 0)

    def test_marcar_como_lido_exige_post(self):
        response = self.client.get(reverse("books:mark_book_as_read", args=[self.lendo.id]))
        self.assertEqual(response.status_code, 405)

    def test_marcar_como_lido_livro_fora_da_estante(self):
        self.client.force_login(self.outro)
        response = self.client.post(reverse("books:mark_book_as_read", args=[self.lendo.id]))
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()["success"])
        self.assertEqual(
            self.BookStatus.objects.get(user=self.user, book=self.lendo).status,
            self.BookStatus.Status.READING,
        )

    def test_clique_no_card_abre_registro_no_livro_sem_seletor(self):
        response = self.client.get(reverse("books:reading_session"))
        self.assertNotContains(response, 'id="rsBook"')  # sem o seletor de livro
        self.assertContains(response, "data-progress-url=")

    def test_salvar_progresso_atualiza_estante(self):
        import json
        from decimal import Decimal
        url = reverse("books:save_reading_progress", args=[self.lendo.id])

        response = self.client.post(url, json.dumps({"percent": 42.5}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        status = self.BookStatus.objects.get(user=self.user, book=self.lendo)
        self.assertEqual(status.reading_progress, Decimal("0.425"))

        profile = self.client.get(reverse("accounts:profile"))
        self.assertContains(profile, "85/200 pág. · 42%")

    def test_salvar_progresso_quero_ler_vira_lendo(self):
        import json
        url = reverse("books:save_reading_progress", args=[self.quero.id])
        self.client.post(url, json.dumps({"percent": 10}), content_type="application/json")
        self.assertEqual(
            self.BookStatus.objects.get(user=self.user, book=self.quero).status,
            self.BookStatus.Status.READING,
        )

    def test_salvar_progresso_invalido(self):
        import json
        url = reverse("books:save_reading_progress", args=[self.lendo.id])
        for body in ({"percent": 150}, {"percent": -1}, {"percent": "abc"}, {}):
            response = self.client.post(url, json.dumps(body), content_type="application/json")
            self.assertEqual(response.status_code, 400)

        self.client.force_login(self.outro)
        response = self.client.post(url, json.dumps({"percent": 10}), content_type="application/json")
        self.assertEqual(response.status_code, 404)
