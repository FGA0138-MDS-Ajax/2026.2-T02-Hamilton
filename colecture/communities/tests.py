from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Community
# Create your tests here.

#teste para Deletar comunidade
class DeleteCommunityTest(TestCase):
    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username='TESTADOR',
            password='teste123'
        )

        self.community = Community.objects.create(
            name='comunidade teste',
            creator=self.user

        )

    #testa se usuario comum não consegue deletar a comunidade
    def test_regular_user_delete_community(self):
        User = get_user_model()
        regular_user = User.objects.create_user(
                username='usuario_comum',
                password='teste123'
        )

        self.client.force_login(regular_user)

        response = self.client.post(
            reverse(
                'communities:delete_community',
                args=[self.community.id]
            )
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            Community.objects.filter(id=self.community.id).exists()
        )

    #testa se o criador da communidade consegue deletar 
    def test_owner_delete_community(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                'communities:delete_community',
                args=[self.community.id]
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Community.objects.filter(id=self.community.id).exists()
        )

#Teste de criação de comunidade

def test_create_community(self):
    self.client.force_login(self.user)

    response = self.client.post(
        reverse('communities:create_community'),
        {
            'name':'Comunidade Teste',
            'description': 'Comunidade para testes',
            'access': Community.Access.PUBLIC,
        }
    )

    self.assertEqual(response.status_code, 302)
    self.assertTrue(
        Community.objects.filter(
            name='Communidade Teste',
            creator=self.user
        ).exists()
    )