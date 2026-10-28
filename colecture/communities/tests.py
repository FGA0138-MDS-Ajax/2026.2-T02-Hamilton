from django.test import TestCase, Client;
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Community, Membership
from datetime import datetime;
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
    
    def test_join_community(self):
        # usuários
        creator_user = get_user_model().objects.create(username="Creator");
        regular_user = get_user_model().objects.create(username="Regular");
        banned_user = get_user_model().objects.create(username="Banned");

        # comunidade
        community_public = Community.objects.create(
            name="Public Community",
            creator=creator_user
        );
        community_private = Community.objects.create(
            name="Private Community",
            creator=creator_user,
            access=Community.Access.PRIVATE
        );
        community_archived = Community.objects.create(
            name="Archived Community",
            creator=creator_user,
            state=Community.State.ARCHIVED
        );

        # memberships
        ban_member = Membership.objects.create(
            community=community_public,
            user=banned_user,
            status=Membership.Status.BANNED
        )

        self.client.force_login(regular_user);

        # entrando em comunidade pública
        response0 = self.client.post(
            reverse(
                "communities:join_community",
                kwargs={"community_id":community_public.id}
            )
        );
        self.assertEqual(response0.status_code, 302);
        new_membership = Membership.objects.filter(
            community=community_public,
            user=regular_user
        );
        self.assertTrue(new_membership.exists());
        self.assertEqual(new_membership.first().role, Membership.Role.MEMBER);
        self.assertEqual(new_membership.first().status, Membership.Status.ACTIVE);

        # entrando em comunidade privada
        response1 = self.client.post(
            reverse(
                "communities:join_community",
                kwargs={"community_id":community_private.id}
            )
        );
        self.assertEqual(response1.status_code, 302);
        new_membership = Membership.objects.filter(
            community=community_private,
            user=regular_user
        );
        self.assertTrue(new_membership.exists());
        self.assertEqual(new_membership.first().role, Membership.Role.NONE);
        self.assertEqual(new_membership.first().status, Membership.Status.PENDING);

        # entrando em comunidade arquivada
        response2 = self.client.post(
            reverse(
                "communities:join_community",
                kwargs={"community_id":community_archived.id}
            )
        );
        self.assertEqual(response2.status_code, 403);
        new_membership = Membership.objects.filter(
            community=community_archived,
            user=regular_user
        );
        self.assertFalse(new_membership.exists());

        # entrando mesmo banido
        self.client.force_login(banned_user);
        response3 = self.client.post(
            reverse(
                "communities:join_community",
                kwargs={"community_id":community_public.id}
            )
        );
        self.assertEqual(response3.status_code, 403);

    def test_leave_community(self):
        # usuários
        creator_user = get_user_model().objects.create(username="Creator");
        moderator_user = get_user_model().objects.create(username="Moderator");
        regular_user = get_user_model().objects.create(username="Regular");

        # comunidade
        community = Community.objects.create(
            name="NewCommunity",
            creator=creator_user
        );
        com_id = community.id;

        # memberships
        mod_member = Membership.objects.create(
            community=community,
            user=moderator_user,
            role=Membership.Role.MODERATOR,
            status=Membership.Status.ACTIVE,
            joined_at=datetime(year=1999, month=12, day=25)
        );
        reg_member = Membership.objects.create(
            community=community,
            user=regular_user,
            role=Membership.Role.MEMBER,
            status=Membership.Status.ACTIVE,
            joined_at=datetime(year=2000, month=10, day=31)
        );

        leave_url = reverse(
            'communities:leave_community',
            kwargs={'community_id':community.id}
        );

        """
        Cenário 1: Criador sai.
        Resposta esperada: Membro mais antigo (o moderador)
        vira criador da comunidade e sua membership é deletada
        """
        self.client.force_login(creator_user);
        creator_left = self.client.post(leave_url);
        community.refresh_from_db();
        self.assertEqual(creator_left.status_code, 302);
        self.assertEqual(community.creator, moderator_user);
        self.assertFalse(Membership.objects.filter(
            community=community,
            user=moderator_user
        ).exists());

        """
        Cenário 2: Regular sai.
        Resposta esperada: Criador continua o mesmo e 
        a membership do regular fica com status "LEFT".
        """
        self.client.force_login(regular_user);
        regular_left = self.client.post(leave_url);
        community.refresh_from_db();
        self.assertEqual(regular_left.status_code, 302);
        self.assertEqual(community.creator, moderator_user);
        self.assertEqual(Membership.objects.filter(
            community=community,
            user=regular_user
        ).first().status, Membership.Status.LEFT);

        """
        Cenário 3: moderador (que agora é criador) sai.
        Resposta esperada: A comunidade é deletada por falta de
        membros.
        """
        self.client.force_login(moderator_user);
        moderator_left = self.client.post(leave_url);
        self.assertEqual(moderator_left.status_code, 302);
        self.assertFalse(Community.objects.filter(
            id=com_id
        ).exists());

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

User = get_user_model()

#teste de visualização da comunidade
class ViewCommunityTest(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username="dono",
            password="teste123"
        )
        self.user = User.objects.create_user(
            username="usuario",
            password="teste123"
        )
        self.admin = User.objects.create_superuser(
            username="admin_view_test",
            email="admin_view_test@example.com",
            password="teste123"
        )

        self.community = Community.objects.create(
            name="Comunidade teste",
            creator=self.owner,
            state=Community.State.ACTIVE
        )

    #usuário comum pode visualizar comunidade ativa
    def test_user_can_view_active_community(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "communities:view_community",
                args=[self.community.id]
            )
        )

        self.assertEqual(response.status_code, 200)

    #usuário comum não pode visualizar comunidade arquivada
    def test_regular_user_cannot_view_archived_community(self):
        self.community.state = Community.State.ARCHIVED
        self.community.save()

        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "communities:view_community",
                args=[self.community.id]
            )
        )

        self.assertEqual(response.status_code, 403)

    #dono pode visualizar comunidade arquivada
    def test_owner_can_view_archived_community(self):
        self.community.state = Community.State.ARCHIVED
        self.community.save()

        self.client.force_login(self.owner)

        response = self.client.get(
            reverse(
                "communities:view_community",
                args=[self.community.id]
            )
        )

        self.assertEqual(response.status_code, 200)

    #administrador pode visualizar comunidade arquivada
    def test_admin_can_view_archived_community(self):
        self.community.state = Community.State.ARCHIVED
        self.community.save()

        self.client.force_login(self.admin)

        response = self.client.get(
            reverse(
                "communities:view_community",
                args=[self.community.id]
            )
        )

        self.assertEqual(response.status_code, 200)


#teste de expulsão e revogação de expulsão de membros da comunidade


class ManageMemberBanTest(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username="dono",
            password="teste123"
        )
        self.moderator = User.objects.create_user(
            username="moderador",
            password="teste123"
        )
        self.user = User.objects.create_user(
            username="membro",
            password="teste123"
        )
        self.unauthorized = User.objects.create_user(
            username="comum",
            password="teste123"
        )

        self.community = Community.objects.create(
            name="Comunidade teste",
            creator=self.owner
        )

        Membership.objects.create(
            user=self.moderator,
            community=self.community,
            role=Membership.Role.MODERATOR,
            status=Membership.Status.ACTIVE
        )

        self.membership = Membership.objects.create(
            user=self.user,
            community=self.community,
            role=Membership.Role.MEMBER,
            status=Membership.Status.ACTIVE
        )

        self.url = reverse(
            "communities:manage_member_ban",
            args=[self.community.id, self.membership.id]
        )

    #usuário sem permissão não pode expulsar um membro
    def test_unauthorized_user_cannot_ban_member(self):
        self.client.force_login(self.unauthorized)

        response = self.client.post(
            self.url,
            {"decision": "ban"}
        )

        self.assertEqual(response.status_code, 403)

        self.membership.refresh_from_db()
        self.assertEqual(
            self.membership.status,
            Membership.Status.ACTIVE
        )

    #moderador pode expulsar um membro ativo
    def test_moderator_can_ban_active_member(self):
        self.client.force_login(self.moderator)

        response = self.client.post(
            self.url,
            {"decision": "ban"}
        )

        self.assertEqual(response.status_code, 302)

        self.membership.refresh_from_db()
        self.assertEqual(
            self.membership.status,
            Membership.Status.BANNED
        )

    #moderador pode revogar a expulsão de um membro banido
    def test_moderator_can_unban_banned_member(self):
        self.membership.status = Membership.Status.BANNED
        self.membership.save()

        self.client.force_login(self.moderator)

        response = self.client.post(
            self.url,
            {"decision": "unban"}
        )

        self.assertEqual(response.status_code, 302)

        self.membership.refresh_from_db()
        self.assertEqual(
            self.membership.status,
            Membership.Status.NONE
        )

    #não pode expulsar membro que não está ativo
    def test_cannot_ban_member_who_is_not_active(self):
        self.membership.status = Membership.Status.PENDING
        self.membership.save()

        self.client.force_login(self.moderator)

        response = self.client.post(
            self.url,
            {"decision": "ban"}
        )

        self.assertEqual(response.status_code, 403)

        self.membership.refresh_from_db()
        self.assertEqual(
            self.membership.status,
            Membership.Status.PENDING
        )

    #não pode revogar expulsão de membro que não está banido
    def test_cannot_unban_member_who_is_not_banned(self):
        self.client.force_login(self.moderator)

        response = self.client.post(
            self.url,
            {"decision": "unban"}
        )

        self.assertEqual(response.status_code, 403)

        self.membership.refresh_from_db()
        self.assertEqual(
            self.membership.status,
            Membership.Status.ACTIVE
        )