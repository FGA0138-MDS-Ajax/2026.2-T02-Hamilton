from django.test import TestCase, Client
from django.urls import reverse;
from django.contrib.auth import get_user_model;

"""
CONSIDERAÇÕES IMPORTANTES:
1. A base de dados é limpa após cada caso
de teste (a cada método).

2. Para rodar os testes, utilize o comando
"python manage.py tests" no terminal.

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
        self.assertEqual(user.first_name, "Linus");
        self.assertEqual(user.last_name, "Torvalds");