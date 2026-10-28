from django.test import TestCase, Client;
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Community, Membership
# Create your tests here.

class CT03(TestCase):
    def setUp(self):
        self.client = Client();

    def test_edit_community_VALID(self):
        # usuários
        creator_user = get_user_model().objects.create(username="Creator");
        moderator_user = get_user_model().objects.create(username="Moderator");

        # comunidade
        community = Community.objects.create(
            name="NewCommunity",
            description="New description",
            creator=creator_user
        );

        # memberships
        mod_member = Membership.objects.create(
            user=moderator_user,
            community=community,
            role=Membership.Role.MODERATOR,
            status=Membership.Status.ACTIVE
        )

        url_edit_community = reverse(
            "communities:edit_community", 
            kwargs={"community_id":community.id}
        );

        valid = [
            # moderador pode editar comunidade.
            { 
                'user':moderator_user, 'name':'Moderator Community', 
                'description':'Moderator description',
                'state':Community.State.ARCHIVED,
                'access':community.access,
            },
            # criador pode editar comunidade.
            { 
                'user':creator_user, 'name':'Creator Community', 
                'description':'Creator description',
                'state':Community.State.ACTIVE,
                'access':Community.Access.PRIVATE,
            },
        ];

        for valid_test in valid:
            self.client.force_login(valid_test['user']);
            response = self.client.post(
                url_edit_community,
                data={
                    'name':valid_test.get('name'),
                    'description':valid_test.get('description'),
                    'state':valid_test.get('state', community.state),
                    'access':valid_test.get('access', community.access),
                }
            );
            community.refresh_from_db();
            self.assertEqual(response.status_code, 302);
            self.assertEqual(community.name, valid_test.get('name'));
            self.assertEqual(community.description, valid_test.get('description'));
            self.assertEqual(community.state, valid_test.get('state'));
            self.assertEqual(community.access, valid_test.get('access'));

    def test_edit_community_INVALID(self):
        # usuários
        creator_user = get_user_model().objects.create(username="Creator");
        moderator_user = get_user_model().objects.create(username="Moderator");
        regular_user = get_user_model().objects.create(username="Regular");

        # comunidade
        community = Community.objects.create(
            name="NewCommunity",
            description="New description",
            creator=creator_user
        );

        # memberships
        mod_member = Membership.objects.create(
            user=moderator_user,
            community=community,
            role=Membership.Role.MODERATOR,
            status=Membership.Status.ACTIVE
        );
        reg_member = Membership.objects.create(
            user=regular_user,
            community=community,
            role=Membership.Role.MEMBER,
            status=Membership.Status.ACTIVE
        )

        url_edit_community = reverse(
            "communities:edit_community", 
            kwargs={"community_id":community.id}
        );

        invalid = [
            # usuário regular não pode editar comunidade
            { 
                'user':regular_user, 'name':'Regular Community', 
                'description':'regular description'
            },
            # "estado" omitido.
            {
                'user':moderator_user, 'name':'Moderator Community', 'state':'',
                'description':'Moderator description',
            },
            # "accesso" de tipo errado
            {
                'user':creator_user, 'name':True, 'access':2,
                'description':'Creator description'
            },
            # tentando atribuir um novo "criador" diretamente
            {
                'user':creator_user, 'name':"Creator Community", 'state':'',
                'description':'Creator description', "creator":moderator_user
            },
        ];

        for invalid_test in invalid:
            self.client.force_login(invalid_test['user']);
            response = self.client.post(
                url_edit_community,
                data={
                    'name':invalid_test.get('name'),
                    'description':invalid_test.get('description'),
                    'state':invalid_test.get('state', community.state),
                    'access':invalid_test.get('access', community.access),
                    'creator':invalid_test.get('creator', '')
                }
            );
            community.refresh_from_db();
            self.assertNotEqual(response.status_code, 302);
            self.assertNotEqual(community.name, invalid_test.get('name'));
            self.assertNotEqual(community.description, invalid_test.get('description'));
            self.assertEqual(community.creator, creator_user);
    


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