from django.test import TestCase, Client;
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Community, Membership
from datetime import datetime, timedelta;
from django.utils import timezone
from django.core.management import call_command
from io import StringIO
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
# (antes era uma função solta, fora de qualquer classe, então o Django nunca
# a executava; o nome esperado também tinha um erro de digitação.)
class CreateCommunityTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='TESTADOR',
            password='teste123'
        )

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
                name='Comunidade Teste',
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


# ---------------------------------------------------------------------------
# CT03 - aceitação/rejeição de membros por solicitação (R09, comunidade privada)
# ---------------------------------------------------------------------------
class MembershipRequestTest(TestCase):
    """
    Fluxo: o leitor solicita entrada em comunidade privada (status PENDING,
    cargo NONE) e um moderador/criador/administrador aceita ou rejeita pela
    view manage_membership_request (POST com decision=accept|reject).
    """

    def setUp(self):
        self.owner = User.objects.create_user(username="dono", password="teste123")
        self.moderator = User.objects.create_user(username="moderador", password="teste123")
        self.member = User.objects.create_user(username="membro", password="teste123")
        self.applicant = User.objects.create_user(username="solicitante", password="teste123")
        self.outsider = User.objects.create_user(username="forasteiro", password="teste123")
        self.admin = User.objects.create_superuser(
            username="admin_request_test",
            email="admin_request_test@example.com",
            password="teste123",
        )

        self.community = Community.objects.create(
            name="Comunidade privada",
            creator=self.owner,
            access=Community.Access.PRIVATE,
        )
        Membership.objects.create(
            user=self.moderator,
            community=self.community,
            role=Membership.Role.MODERATOR,
            status=Membership.Status.ACTIVE,
        )
        self.member_membership = Membership.objects.create(
            user=self.member,
            community=self.community,
            role=Membership.Role.MEMBER,
            status=Membership.Status.ACTIVE,
        )

        # joined_at antigo para provar que o aceite o renova
        self.old_date = timezone.now() - timedelta(days=365)
        self.pending = Membership.objects.create(
            user=self.applicant,
            community=self.community,
            role=Membership.Role.NONE,
            status=Membership.Status.PENDING,
            joined_at=self.old_date,
        )

        self.url = reverse(
            "communities:manage_membership_request",
            args=[self.community.id, self.pending.id],
        )
        self.community_url = reverse(
            "communities:view_community", args=[self.community.id]
        )

    def decide(self, user, decision="accept", url=None):
        self.client.force_login(user)
        data = {} if decision is None else {"decision": decision}
        return self.client.post(url or self.url, data)

    def assert_still_pending(self):
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, Membership.Status.PENDING)
        self.assertEqual(self.pending.role, Membership.Role.NONE)

    # ---------- aceitar ----------

    # moderador aceita: vira membro ativo com cargo MEMBER
    def test_moderator_can_accept_request(self):
        response = self.decide(self.moderator, "accept")

        self.assertRedirects(response, self.community_url, fetch_redirect_response=False)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, Membership.Status.ACTIVE)
        self.assertEqual(self.pending.role, Membership.Role.MEMBER)
        self.assertGreater(self.pending.joined_at, self.old_date)

    # criador e administrador também podem aceitar
    def test_owner_and_admin_can_accept_request(self):
        for user in (self.owner, self.admin):
            with self.subTest(user=user.username):
                self.pending.status = Membership.Status.PENDING
                self.pending.role = Membership.Role.NONE
                self.pending.save()

                response = self.decide(user, "accept")

                self.assertEqual(response.status_code, 302)
                self.pending.refresh_from_db()
                self.assertEqual(self.pending.status, Membership.Status.ACTIVE)
                self.assertEqual(self.pending.role, Membership.Role.MEMBER)

    # ---------- rejeitar ----------

    # rejeitar não torna o usuário membro, mas mantém a linha (constraint única)
    def test_moderator_can_reject_request(self):
        response = self.decide(self.moderator, "reject")

        self.assertRedirects(response, self.community_url, fetch_redirect_response=False)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, Membership.Status.NONE)
        self.assertEqual(self.pending.role, Membership.Role.NONE)
        self.assertEqual(
            Membership.objects.filter(
                user=self.applicant, community=self.community
            ).count(),
            1,
        )

    # quem foi rejeitado pode pedir de novo e volta a PENDING
    def test_rejected_user_can_request_again(self):
        self.decide(self.moderator, "reject")

        self.client.force_login(self.applicant)
        response = self.client.post(
            reverse("communities:join_community", args=[self.community.id])
        )

        self.assertEqual(response.status_code, 302)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, Membership.Status.PENDING)

    # fluxo completo: solicitar pela view de entrada e então aceitar
    def test_full_flow_request_then_accept(self):
        newcomer = User.objects.create_user(username="novato", password="teste123")

        self.client.force_login(newcomer)
        self.client.post(reverse("communities:join_community", args=[self.community.id]))
        membership = Membership.objects.get(user=newcomer, community=self.community)
        self.assertEqual(membership.status, Membership.Status.PENDING)

        url = reverse(
            "communities:manage_membership_request",
            args=[self.community.id, membership.id],
        )
        self.decide(self.moderator, "accept", url=url)

        membership.refresh_from_db()
        self.assertEqual(membership.status, Membership.Status.ACTIVE)
        self.assertEqual(membership.role, Membership.Role.MEMBER)

    # ---------- restrição de perfil ----------

    # membro comum, forasteiro e o próprio solicitante não decidem solicitações
    def test_users_without_permission_cannot_decide(self):
        for user in (self.member, self.outsider, self.applicant):
            for decision in ("accept", "reject"):
                with self.subTest(user=user.username, decision=decision):
                    response = self.decide(user, decision)
                    self.assertEqual(response.status_code, 403)
                    self.assert_still_pending()

    # moderador de OUTRA comunidade não tem poder sobre esta
    def test_moderator_of_another_community_cannot_decide(self):
        other = Community.objects.create(name="Outra", creator=self.outsider)
        Membership.objects.create(
            user=self.member,
            community=other,
            role=Membership.Role.MODERATOR,
            status=Membership.Status.ACTIVE,
        )

        response = self.decide(self.member, "accept")

        self.assertEqual(response.status_code, 403)
        self.assert_still_pending()

    # moderador banido (cargo antigo, status BANNED) perde o poder
    def test_banned_moderator_cannot_decide(self):
        banned = User.objects.create_user(username="mod_banido", password="teste123")
        Membership.objects.create(
            user=banned,
            community=self.community,
            role=Membership.Role.MODERATOR,
            status=Membership.Status.BANNED,
        )

        response = self.decide(banned, "accept")

        self.assertEqual(response.status_code, 403)
        self.assert_still_pending()

    # usuário deslogado é mandado para o login e nada muda
    def test_anonymous_is_redirected_to_login(self):
        response = self.client.post(self.url, {"decision": "accept"})

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)
        self.assert_still_pending()

    # ---------- entradas inválidas ----------

    # decisão desconhecida ou ausente é recusada
    def test_invalid_decision_is_rejected(self):
        for decision in ("approve", "ACCEPT", "ban", "", None):
            with self.subTest(decision=decision):
                response = self.decide(self.moderator, decision)
                self.assertEqual(response.status_code, 403)
                self.assert_still_pending()

    # só POST altera dados
    def test_get_is_not_allowed(self):
        self.client.force_login(self.moderator)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)
        self.assert_still_pending()

    # o endpoint só trata solicitações PENDING: não serve para remover
    # membro ativo nem para desbanir
    def test_only_pending_requests_can_be_decided(self):
        banned = User.objects.create_user(username="banido", password="teste123")
        banned_membership = Membership.objects.create(
            user=banned,
            community=self.community,
            role=Membership.Role.MEMBER,
            status=Membership.Status.BANNED,
        )

        cases = [
            (self.member_membership, Membership.Status.ACTIVE),
            (banned_membership, Membership.Status.BANNED),
        ]
        for membership, expected_status in cases:
            for decision in ("accept", "reject"):
                with self.subTest(status=expected_status, decision=decision):
                    url = reverse(
                        "communities:manage_membership_request",
                        args=[self.community.id, membership.id],
                    )
                    response = self.decide(self.moderator, decision, url=url)

                    self.assertEqual(response.status_code, 403)
                    membership.refresh_from_db()
                    self.assertEqual(membership.status, expected_status)

    # membership de outra comunidade na URL desta -> 404
    def test_membership_from_another_community_returns_404(self):
        other = Community.objects.create(
            name="Outra privada",
            creator=self.owner,
            access=Community.Access.PRIVATE,
        )
        other_pending = Membership.objects.create(
            user=self.outsider,
            community=other,
            role=Membership.Role.NONE,
            status=Membership.Status.PENDING,
        )
        url = reverse(
            "communities:manage_membership_request",
            args=[self.community.id, other_pending.id],
        )

        response = self.decide(self.moderator, "accept", url=url)

        self.assertEqual(response.status_code, 404)
        other_pending.refresh_from_db()
        self.assertEqual(other_pending.status, Membership.Status.PENDING)


# ---------------------------------------------------------------------------
# CT03 - edição de cargos de membros (R09: promover a moderador / rebaixar)
# ---------------------------------------------------------------------------
class MemberRoleEditTest(TestCase):
    """
    A view edit_member_role recebe POST com role=MEMBER|MODERATOR.
    Quem edita: administrador, criador ou moderador ATIVO da comunidade.
    Alvo: apenas membros ATIVOS.
    """

    def setUp(self):
        self.owner = User.objects.create_user(username="dono", password="teste123")
        self.moderator = User.objects.create_user(username="moderador", password="teste123")
        self.other_moderator = User.objects.create_user(username="moderador2", password="teste123")
        self.member = User.objects.create_user(username="membro", password="teste123")
        self.outsider = User.objects.create_user(username="forasteiro", password="teste123")
        self.admin = User.objects.create_superuser(
            username="admin_role_test",
            email="admin_role_test@example.com",
            password="teste123",
        )

        self.community = Community.objects.create(name="Comunidade", creator=self.owner)

        Membership.objects.create(
            user=self.moderator,
            community=self.community,
            role=Membership.Role.MODERATOR,
            status=Membership.Status.ACTIVE,
        )
        self.mod_target = Membership.objects.create(
            user=self.other_moderator,
            community=self.community,
            role=Membership.Role.MODERATOR,
            status=Membership.Status.ACTIVE,
        )
        self.target = Membership.objects.create(
            user=self.member,
            community=self.community,
            role=Membership.Role.MEMBER,
            status=Membership.Status.ACTIVE,
        )

        self.community_url = reverse(
            "communities:view_community", args=[self.community.id]
        )

    def url_for(self, membership):
        return reverse(
            "communities:edit_member_role",
            args=[membership.community_id, membership.id],
        )

    def set_role(self, user, membership, role="MODERATOR"):
        self.client.force_login(user)
        data = {} if role is None else {"role": role}
        return self.client.post(self.url_for(membership), data)

    def assert_role(self, membership, expected_role, expected_status=Membership.Status.ACTIVE):
        membership.refresh_from_db()
        self.assertEqual(membership.role, expected_role)
        self.assertEqual(membership.status, expected_status)

    # ---------- cargo válido ----------

    # moderador promove membro a moderador
    def test_moderator_can_promote_member(self):
        response = self.set_role(self.moderator, self.target, Membership.Role.MODERATOR)

        self.assertRedirects(response, self.community_url, fetch_redirect_response=False)
        self.assert_role(self.target, Membership.Role.MODERATOR)

    # criador e administrador também promovem
    def test_owner_and_admin_can_promote_member(self):
        for user in (self.owner, self.admin):
            with self.subTest(user=user.username):
                self.target.role = Membership.Role.MEMBER
                self.target.save()

                response = self.set_role(user, self.target, Membership.Role.MODERATOR)

                self.assertEqual(response.status_code, 302)
                self.assert_role(self.target, Membership.Role.MODERATOR)

    # rebaixar moderador a membro (por moderador, criador ou admin)
    def test_can_demote_moderator_to_member(self):
        for user in (self.moderator, self.owner, self.admin):
            with self.subTest(user=user.username):
                self.mod_target.role = Membership.Role.MODERATOR
                self.mod_target.save()

                response = self.set_role(user, self.mod_target, Membership.Role.MEMBER)

                self.assertEqual(response.status_code, 302)
                self.assert_role(self.mod_target, Membership.Role.MEMBER)

    # repetir o mesmo cargo é aceito e não muda nada
    def test_setting_same_role_is_accepted(self):
        response = self.set_role(self.moderator, self.target, Membership.Role.MEMBER)

        self.assertEqual(response.status_code, 302)
        self.assert_role(self.target, Membership.Role.MEMBER)

    # só o cargo muda: campos extras (status, user, community) são ignorados
    def test_only_role_is_changed(self):
        self.client.force_login(self.moderator)

        response = self.client.post(
            self.url_for(self.target),
            {
                "role": Membership.Role.MODERATOR,
                "status": Membership.Status.BANNED,
                "user": self.outsider.id,
                "community": 9999,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.target.refresh_from_db()
        self.assertEqual(self.target.role, Membership.Role.MODERATOR)
        self.assertEqual(self.target.status, Membership.Status.ACTIVE)
        self.assertEqual(self.target.user, self.member)
        self.assertEqual(self.target.community, self.community)

    # ---------- cargo inválido ----------

    # nenhum valor fora de MEMBER/MODERATOR é aceito
    def test_invalid_roles_are_rejected(self):
        invalid_roles = [
            Membership.Role.NONE,  # existe no model, mas não é cargo atribuível
            "OWNER",
            "CREATOR",
            "ADMIN",
            "moderator",           # diferença de caixa
            " MODERATOR",          # espaço sobrando
            "",
            None,                  # campo ausente
        ]
        for role in invalid_roles:
            with self.subTest(role=role):
                response = self.set_role(self.moderator, self.target, role)

                self.assertEqual(response.status_code, 403)
                self.assert_role(self.target, Membership.Role.MEMBER)

    # ---------- restrição de perfil ----------

    # membro comum não altera cargos, nem o próprio (escalada de privilégio)
    def test_regular_member_cannot_edit_roles(self):
        for membership in (self.target, self.mod_target):
            with self.subTest(target=membership.user.username):
                response = self.set_role(self.member, membership, Membership.Role.MODERATOR)
                self.assertEqual(response.status_code, 403)

        self.assert_role(self.target, Membership.Role.MEMBER)
        self.assert_role(self.mod_target, Membership.Role.MODERATOR)

    # forasteiro (sem membership) não altera cargos
    def test_outsider_cannot_edit_roles(self):
        response = self.set_role(self.outsider, self.target, Membership.Role.MODERATOR)

        self.assertEqual(response.status_code, 403)
        self.assert_role(self.target, Membership.Role.MEMBER)

    # moderador cujo status não é ACTIVE (pendente, saiu, banido) perde o poder
    def test_non_active_moderator_cannot_edit_roles(self):
        for status in (
            Membership.Status.PENDING,
            Membership.Status.LEFT,
            Membership.Status.BANNED,
        ):
            with self.subTest(status=status):
                user = User.objects.create_user(username=f"mod_{status}", password="teste123")
                Membership.objects.create(
                    user=user,
                    community=self.community,
                    role=Membership.Role.MODERATOR,
                    status=status,
                )

                response = self.set_role(user, self.target, Membership.Role.MODERATOR)

                self.assertEqual(response.status_code, 403)
                self.assert_role(self.target, Membership.Role.MEMBER)

    # moderador de outra comunidade não tem poder aqui
    def test_moderator_of_another_community_cannot_edit_roles(self):
        other = Community.objects.create(name="Outra", creator=self.outsider)
        Membership.objects.create(
            user=self.member,
            community=other,
            role=Membership.Role.MODERATOR,
            status=Membership.Status.ACTIVE,
        )

        response = self.set_role(self.member, self.target, Membership.Role.MODERATOR)

        self.assertEqual(response.status_code, 403)
        self.assert_role(self.target, Membership.Role.MEMBER)

    # ---------- alvo inválido ----------

    # só membros ativos têm cargo editável
    def test_cannot_edit_role_of_non_active_members(self):
        for status in (
            Membership.Status.PENDING,
            Membership.Status.LEFT,
            Membership.Status.BANNED,
        ):
            with self.subTest(status=status):
                user = User.objects.create_user(username=f"alvo_{status}", password="teste123")
                membership = Membership.objects.create(
                    user=user,
                    community=self.community,
                    role=Membership.Role.NONE,
                    status=status,
                )

                response = self.set_role(self.moderator, membership, Membership.Role.MODERATOR)

                self.assertEqual(response.status_code, 403)
                self.assert_role(membership, Membership.Role.NONE, expected_status=status)

    # membership de outra comunidade na URL desta -> 404
    def test_membership_from_another_community_returns_404(self):
        other = Community.objects.create(name="Outra", creator=self.owner)
        other_membership = Membership.objects.create(
            user=self.outsider,
            community=other,
            role=Membership.Role.MEMBER,
            status=Membership.Status.ACTIVE,
        )
        url = reverse(
            "communities:edit_member_role",
            args=[self.community.id, other_membership.id],  # comunidade errada
        )
        self.client.force_login(self.moderator)

        response = self.client.post(url, {"role": Membership.Role.MODERATOR})

        self.assertEqual(response.status_code, 404)
        self.assert_role(other_membership, Membership.Role.MEMBER)

    # ---------- método / autenticação ----------

    # só POST altera dados
    def test_get_is_not_allowed(self):
        self.client.force_login(self.moderator)

        response = self.client.get(self.url_for(self.target))

        self.assertEqual(response.status_code, 403)
        self.assert_role(self.target, Membership.Role.MEMBER)

    # deslogado vai para o login e nada muda
    def test_anonymous_is_redirected_to_login(self):
        response = self.client.post(
            self.url_for(self.target), {"role": Membership.Role.MODERATOR}
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)
        self.assert_role(self.target, Membership.Role.MEMBER)


# ---------------------------------------------------------------------------
# Purge de comunidades arquivadas (retenção de 60 dias)
# ---------------------------------------------------------------------------
class PurgeArchivedCommunitiesTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="dono", password="teste123")

    def make_archived(self, name, days_ago):
        community = Community.objects.create(
            name=name,
            creator=self.owner,
            state=Community.State.ARCHIVED,  # o save() preenche archived_at com "agora"
        )
        # update() não passa pelo save(), então a data antiga não é sobrescrita
        Community.objects.filter(pk=community.pk).update(
            archived_at=timezone.now() - timedelta(days=days_ago)
        )
        return community

    def run_purge(self):
        out = StringIO()
        call_command("purge_archived_communities", stdout=out)
        return out.getvalue()

    # exclui só a arquivada há mais de 60 dias; recente e ativa ficam
    def test_purge_only_deletes_expired_archived(self):
        old = self.make_archived("Velha", days_ago=61)
        recent = self.make_archived("Recente", days_ago=59)
        active = Community.objects.create(name="Ativa", creator=self.owner)

        self.run_purge()

        self.assertFalse(Community.objects.filter(pk=old.pk).exists())
        self.assertTrue(Community.objects.filter(pk=recent.pk).exists())
        self.assertTrue(Community.objects.filter(pk=active.pk).exists())

    # os memberships da comunidade excluída saem em cascata
    def test_purge_removes_memberships_of_deleted_community(self):
        old = self.make_archived("Velha", days_ago=90)
        member = User.objects.create_user(username="membro", password="teste123")
        Membership.objects.create(
            user=member,
            community=old,
            role=Membership.Role.MEMBER,
            status=Membership.Status.ACTIVE,
        )

        self.run_purge()

        self.assertFalse(Membership.objects.filter(community_id=old.pk).exists())
        # o usuário não é apagado junto
        self.assertTrue(User.objects.filter(pk=member.pk).exists())

    # comunidade desarquivada deixa de ser candidata ao purge
    def test_unarchived_community_is_not_purged(self):
        community = self.make_archived("Restaurada", days_ago=90)
        community.refresh_from_db()
        community.state = Community.State.ACTIVE
        community.save()  # o save() zera archived_at

        self.run_purge()

        community.refresh_from_db()
        self.assertIsNone(community.archived_at)
        self.assertTrue(Community.objects.filter(pk=community.pk).exists())

    # sem nada vencido, o comando roda sem erro e informa 0
    def test_purge_with_nothing_to_delete(self):
        Community.objects.create(name="Ativa", creator=self.owner)

        output = self.run_purge()

        self.assertIn("0 comunidade(s)", output)
        self.assertEqual(Community.objects.count(), 1)

    # rodar duas vezes seguidas não causa erro nem exclui a mais
    def test_purge_is_idempotent(self):
        self.make_archived("Velha", days_ago=61)
        keep = self.make_archived("Recente", days_ago=10)

        self.run_purge()
        output = self.run_purge()

        self.assertIn("0 comunidade(s)", output)
        self.assertTrue(Community.objects.filter(pk=keep.pk).exists())