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