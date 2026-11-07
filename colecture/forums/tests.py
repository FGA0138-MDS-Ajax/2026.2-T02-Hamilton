from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model;
from .models import Forum, Message, FORUM_NAME_MAX_LENGTH

from communities.models import Community, Membership;
from communities.services import CommunityService, MembershipService;
from goals.models import Goal, GoalParticipation;
from goals.services import GoalService;
from accounts.services import AccountService;

import importlib;
from django.apps import apps;

# Create your tests here.

# ---------------------------------------------------------------------------
# CT04 - criação de comunidade e parentesco
# ---------------------------------------------------------------------------
class ForumCreation(TestCase):
    # com o setUpTestData, cada método irá retornar
    # a base de dados para o estado definido aqui.
    @classmethod
    def setUpTestData(cls):
        cls.client = Client();
        cls.com_owner = AccountService.create_account(
            get_user_model().objects.create(
                username='CommunityOwner'
            )
        );
        cls.community = CommunityService.create_community(Community.objects.create(
            name='NewCommunity',
            creator=cls.com_owner
        ));
        cls.community_goal = GoalService.create_goal(Goal.objects.create(
            name='Read 1500 pages',
            owner_community=cls.community,
            goal_type=Goal.GoalType.PAGE_COUNT,
            target=1500,
        ), cls.community);
        cls.user_goal = GoalService.create_goal(Goal.objects.create(
            name='Read for 2 hours',
            owner_profile=cls.com_owner.profile,
            goal_type=Goal.GoalType.HOUR_COUNT,
            target=2
        ), cls.com_owner.profile);
        

    def test_forums_creation(self):
        # forum principal de comunidade e de meta
        # são criados
        self.assertIsNotNone(self.community.forum);
        self.assertIsNotNone(self.community_goal.forum);

        # forum de meta individual não é criado.
        with self.assertRaises(Forum.DoesNotExist):
            _ = self.user_goal.forum;

    def test_exclusive_forum_parenting(self):
        # meta de comunidade só tem pai comunidade
        com_goal_c_parent = self.community_goal.owner_community!=None;
        com_goal_p_parent = self.community_goal.owner_profile!=None;

        # meta de perfil só tem pai perfil
        prof_goal_c_parent = self.user_goal.owner_community!=None;
        prof_goal_p_parent = self.user_goal.owner_profile!=None;

        self.assertTrue(com_goal_c_parent and not com_goal_p_parent);
        self.assertTrue(prof_goal_p_parent and not prof_goal_c_parent);

# ---------------------------------------------------------------------------
# CT04 - envio e exclusão de mensagens
# ---------------------------------------------------------------------------
class ForumMessages(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client();

        # criando contas
        cls.admin_acc = AccountService.create_account(
            get_user_model().objects.create_superuser(
                username='Admin'
            )
        );
        cls.com_owner = AccountService.create_account(
            get_user_model().objects.create(
                username='CommunityOwner'
            )
        );
        cls.participant = AccountService.create_account(
            get_user_model().objects.create(
                username='Participant'
            )
        );
        cls.goal_participant = AccountService.create_account(
            get_user_model().objects.create(
                username='G Participant'
            )
        );
        cls.outsider = AccountService.create_account(
            get_user_model().objects.create(
                username='Outsider'
            )
        );

        # criando comunidade e meta
        cls.community = CommunityService.create_community(Community.objects.create(
            name='NewCommunity',
            creator=cls.com_owner
        ));
        cls.community_goal = GoalService.create_goal(Goal.objects.create(
            name='Read 1500 pages',
            owner_community=cls.community,
            goal_type=Goal.GoalType.PAGE_COUNT,
            target=1500,
        ), cls.community);

        # criando conexões

        # participant participa apenas da comunidade,
        # não da meta ainda
        MembershipService.enter_community(
            cls.participant,
            cls.community,
        );
        # goal participant participa da comunidade e
        # da meta
        MembershipService.enter_community(
            cls.goal_participant,
            cls.community,
        );
        GoalService.join(
            cls.goal_participant,
            cls.community_goal
        );

        cls.community_forum = cls.community.forum;
        cls.goal_forum = cls.community_goal.forum;

        cls.part_message = Message.objects.create(
            forum=cls.community_forum,
            author=cls.participant,
            content='Super different message'
        );

    # ===== ENVIANDO MENSAGENS =====
    def test_participant_message_community(self):
        # apenas membros de uma comunidade podem
        # enviar mensagens no fórum principal dela.

        # login na conta do participante
        self.client.force_login(self.participant);

        message_sent = "Acaba pelo amor de Deus";

        # tenta mandar mensagem
        response = self.client.post(
            reverse(
                "forums:view_forum", 
                kwargs={'forum_id':self.community_forum.id}
            ),
            data={
                'content':message_sent
            }
        );

        self.assertEqual(response.status_code, 302);
        self.assertTrue(
            Message.objects.filter(
                author=self.participant,
                forum=self.community_forum,
                content=message_sent
            ).exists()
        );
    
    def test_outsider_message_community(self):
        # estrangeiros não podem mandar mensagens
        # no fórum

        # login na conta do estrangeiro
        self.client.force_login(self.outsider);

        message_sent = "Acaba pelo amor de Deus";

        # tenta mandar mensagem
        response = self.client.post(
            reverse(
                "forums:view_forum", 
                kwargs={'forum_id':self.community_forum.id}
            ),
            data={
                'content':message_sent
            }
        );

        # será barrado
        self.assertEqual(response.status_code, 403);
        self.assertFalse(
            Message.objects.filter(
                author=self.outsider,
                forum=self.community_forum,
                content=message_sent
            ).exists()
        );

    def test_participant_message_goal(self):
        # participantes da meta podem enviar mensagens
        # no fórum

        # login na conta do participante da meta
        self.client.force_login(self.goal_participant);

        message_sent = "Acaba pelo amor de Deus";

        # tenta mandar mensagem
        response = self.client.post(
            reverse(
                "forums:view_forum", 
                kwargs={'forum_id':self.goal_forum.id}
            ),
            data={
                'content':message_sent
            }
        );

        # será aceito
        self.assertEqual(response.status_code, 302);
        self.assertTrue(
            Message.objects.filter(
                author=self.goal_participant,
                forum=self.goal_forum,
                content=message_sent
            ).exists()
        );

    def test_non_participant_message_goal(self):
        # não participantes da meta não podem enviar
        # mensagens no fórum da meta.

        # login na conta do participante da comunidade
        # que não é participante da meta.
        self.client.force_login(self.participant);

        message_sent = "Acaba pelo amor de Deus";

        # tenta mandar mensagem
        response = self.client.post(
            reverse(
                "forums:view_forum", 
                kwargs={'forum_id':self.goal_forum.id}
            ),
            data={
                'content':message_sent
            }
        );

        # será barrado
        self.assertEqual(response.status_code, 403);
        self.assertFalse(
            Message.objects.filter(
                author=self.participant,
                forum=self.goal_forum,
                content=message_sent
            ).exists()
        );


    # ===== DELETANDO MENSAGENS =====
    def test_mod_deleting_messages(self):
        # moderadores e criador da comunidade podem
        # deletar as mensagens mesmo sem ter criado-as.

        # login com o criador da comunidade
        self.client.force_login(self.com_owner);

        old_message = self.part_message;
        old_author = old_message.author;
        old_forum = old_message.forum;

        response = self.client.post(
            reverse(
                "forums:delete_message", 
                kwargs={'message_id':old_message.id}
            ),
        );

        self.assertEqual(response.status_code, 302);
        self.assertFalse(
            Message.objects.filter(
                author=old_author,
                forum=old_forum
            ).exists()
        );

    def test_admin_deleting_messages(self):
        # admins podem deletar mensagens mesmo
        # sem participar da comunidade

        # login com o admin
        self.client.force_login(self.admin_acc);

        old_message = self.part_message;
        old_author = old_message.author;
        old_forum = old_message.forum;

        response = self.client.post(
            reverse(
                "forums:delete_message", 
                kwargs={'message_id':old_message.id}
            ),
        );

        self.assertEqual(response.status_code, 302);
        self.assertFalse(
            Message.objects.filter(
                author=old_author,
                forum=old_forum
            ).exists()
        );

    def test_outsider_deleting_messages(self):
        # estrangeiros não podem deletar mensagens

        # login com o estrangeiro
        self.client.force_login(self.outsider);

        old_message = self.part_message;
        old_author = old_message.author;
        old_forum = old_message.forum;

        response = self.client.post(
            reverse(
                "forums:delete_message", 
                kwargs={'message_id':old_message.id}
            ),
        );

        self.assertEqual(response.status_code, 403);
        self.assertTrue(
            Message.objects.filter(
                author=old_author,
                forum=old_forum
            ).exists()
        );
     
    def test_message_owner_deleting_messages(self):
        # dono da mensagem pode deletá-la

        # login com o dono
        self.client.force_login(self.participant);

        old_message = self.part_message;
        old_author = old_message.author;
        old_forum = old_message.forum;

        response = self.client.post(
            reverse(
                "forums:delete_message", 
                kwargs={'message_id':old_message.id}
            ),
        );

        self.assertEqual(response.status_code, 302);
        self.assertFalse(
            Message.objects.filter(
                author=old_author,
                forum=old_forum
            ).exists()
        );
    
    def test_message_viewer_deleting_messages(self):
        # visualizador (não moderador) e não dono
        # não pode deletar a mensagem

        # login com o visualizador (goal participant
        # não é dono da mensagem)
        self.client.force_login(self.goal_participant);

        old_message = self.part_message;
        old_author = old_message.author;
        old_forum = old_message.forum;

        response = self.client.post(
            reverse(
                "forums:delete_message", 
                kwargs={'message_id':old_message.id}
            ),
        );

        self.assertEqual(response.status_code, 403);
        self.assertTrue(
            Message.objects.filter(
                author=old_author,
                forum=old_forum
            ).exists()
        );


# ---------------------------------------------------------------------------
# CT04 - acesso aos fóruns (geral da comunidade e próprio de cada meta)
# ---------------------------------------------------------------------------
class ForumAccess(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model();
        cls.admin_acc = AccountService.create_account(
            User.objects.create_superuser(username='Admin')
        );
        cls.com_owner = AccountService.create_account(
            User.objects.create(username='CommunityOwner')
        );
        cls.moderator = AccountService.create_account(
            User.objects.create(username='Moderator')
        );
        cls.member = AccountService.create_account(
            User.objects.create(username='Member')
        );
        cls.goal_participant = AccountService.create_account(
            User.objects.create(username='GoalParticipant')
        );
        cls.outsider = AccountService.create_account(
            User.objects.create(username='Outsider')
        );

        cls.community = CommunityService.create_community(Community.objects.create(
            name='NewCommunity',
            creator=cls.com_owner
        ));
        cls.community_goal = GoalService.create_goal(Goal.objects.create(
            name='Read 1500 pages',
            owner_community=cls.community,
            goal_type=Goal.GoalType.PAGE_COUNT,
            target=1500,
        ), cls.community);
        cls.user_goal = GoalService.create_goal(Goal.objects.create(
            name='Read for 2 hours',
            owner_profile=cls.com_owner.profile,
            goal_type=Goal.GoalType.HOUR_COUNT,
            target=2
        ), cls.com_owner.profile);

        MembershipService.enter_community(
            cls.moderator, cls.community, role=Membership.Role.MODERATOR
        );
        MembershipService.enter_community(cls.member, cls.community);
        MembershipService.enter_community(cls.goal_participant, cls.community);
        GoalService.join(cls.goal_participant, cls.community_goal);

        cls.community_forum = cls.community.forum;
        cls.goal_forum = cls.community_goal.forum;

    def forum_url(self, forum):
        return reverse("forums:view_forum", kwargs={'forum_id':forum.id});

    # ===== VISUALIZAÇÃO =====
    def test_community_forum_is_visible_to_members_only(self):
        # membros veem o fórum geral; estrangeiros não
        self.client.force_login(self.member);
        self.assertEqual(self.client.get(self.forum_url(self.community_forum)).status_code, 200);

        self.client.force_login(self.outsider);
        self.assertEqual(self.client.get(self.forum_url(self.community_forum)).status_code, 403);

    def test_goal_forum_is_visible_to_participants_only(self):
        # só quem participa da meta vê o fórum dela, mesmo
        # sendo membro da comunidade
        self.client.force_login(self.goal_participant);
        self.assertEqual(self.client.get(self.forum_url(self.goal_forum)).status_code, 200);

        self.client.force_login(self.member);
        self.assertEqual(self.client.get(self.forum_url(self.goal_forum)).status_code, 403);

        self.client.force_login(self.outsider);
        self.assertEqual(self.client.get(self.forum_url(self.goal_forum)).status_code, 403);

    def test_managers_can_view_every_forum_of_the_community(self):
        # criador, moderador e admin entram nos dois fóruns
        # mesmo sem participar da meta
        for user in (self.com_owner, self.moderator, self.admin_acc):
            self.client.force_login(user);
            for forum in (self.community_forum, self.goal_forum):
                with self.subTest(user=user.username, forum=forum.name):
                    response = self.client.get(self.forum_url(forum));
                    self.assertEqual(response.status_code, 200);

    def test_anonymous_is_sent_to_login(self):
        response = self.client.get(self.forum_url(self.community_forum));
        self.assertEqual(response.status_code, 302);
        self.assertTrue(response.url.startswith(reverse("accounts:login")));

    def test_archived_community_forum_is_closed_to_non_managers(self):
        # mesma regra da página da comunidade: arquivada = só quem gerencia
        Community.objects.filter(pk=self.community.pk).update(
            state=Community.State.ARCHIVED
        );

        self.client.force_login(self.member);
        self.assertEqual(self.client.get(self.forum_url(self.community_forum)).status_code, 403);
        self.client.force_login(self.goal_participant);
        self.assertEqual(self.client.get(self.forum_url(self.goal_forum)).status_code, 403);

        self.client.force_login(self.com_owner);
        self.assertEqual(self.client.get(self.forum_url(self.community_forum)).status_code, 200);

    def test_messages_are_listed_oldest_first_with_author(self):
        first = Message.objects.create(
            forum=self.community_forum, author=self.member, content='primeira'
        );
        second = Message.objects.create(
            forum=self.community_forum, author=self.com_owner, content='segunda'
        );

        self.client.force_login(self.member);
        response = self.client.get(self.forum_url(self.community_forum));

        self.assertEqual(list(response.context['forum_messages']), [first, second]);
        self.assertContains(response, 'primeira');
        self.assertContains(response, self.com_owner.username);

    def test_messages_of_one_forum_do_not_leak_to_the_other(self):
        Message.objects.create(
            forum=self.community_forum, author=self.member, content='so no geral'
        );
        Message.objects.create(
            forum=self.goal_forum, author=self.goal_participant, content='so na meta'
        );

        self.client.force_login(self.goal_participant);
        response = self.client.get(self.forum_url(self.goal_forum));

        self.assertContains(response, 'so na meta');
        self.assertNotContains(response, 'so no geral');

    # ===== ENVIO =====
    def test_invalid_message_is_rejected_and_form_is_shown_again(self):
        self.client.force_login(self.member);
        response = self.client.post(
            self.forum_url(self.community_forum), data={'content':''}
        );

        self.assertEqual(response.status_code, 400);
        self.assertTemplateUsed(response, "communities/forum.html");
        self.assertFalse(Message.objects.filter(forum=self.community_forum).exists());

    def test_locked_forum_does_not_accept_messages(self):
        Forum.objects.filter(pk=self.community_forum.pk).update(
            state=Forum.State.LOCKED
        );

        self.client.force_login(self.member);
        response = self.client.post(
            self.forum_url(self.community_forum), data={'content':'oi'}
        );

        # volta para o fórum (página normal) com um aviso, sem salvar nada
        self.assertRedirects(
            response, self.forum_url(self.community_forum), fetch_redirect_response=False
        );
        self.assertFalse(Message.objects.filter(forum=self.community_forum).exists());

        page = self.client.get(self.forum_url(self.community_forum));
        self.assertEqual(page.status_code, 200);
        self.assertContains(page, "Este fórum está trancado. Não é possível enviar mensagens.");

    def test_locked_forum_keeps_messages_and_warns_on_delete(self):
        message = Message.objects.create(
            forum=self.community_forum, author=self.member, content='fica'
        );
        Forum.objects.filter(pk=self.community_forum.pk).update(
            state=Forum.State.LOCKED
        );

        self.client.force_login(self.member);
        response = self.client.post(
            reverse("forums:delete_message", kwargs={'message_id':message.id})
        );

        self.assertRedirects(
            response, self.forum_url(self.community_forum), fetch_redirect_response=False
        );
        self.assertTrue(Message.objects.filter(pk=message.pk).exists());

        page = self.client.get(self.forum_url(self.community_forum));
        self.assertContains(page, "Este fórum está trancado. Não é possível apagar mensagens.");

    # ===== MODERAÇÃO =====
    def test_moderator_deletes_message_of_goal_forum(self):
        # o fórum da meta encontra a comunidade pela meta (owner_community)
        message = Message.objects.create(
            forum=self.goal_forum, author=self.goal_participant, content='apagar'
        );

        self.client.force_login(self.moderator);
        response = self.client.post(
            reverse("forums:delete_message", kwargs={'message_id':message.id})
        );

        self.assertEqual(response.status_code, 302);
        self.assertFalse(Message.objects.filter(pk=message.pk).exists());

    def test_anonymous_cannot_delete_message(self):
        message = Message.objects.create(
            forum=self.community_forum, author=self.member, content='fica'
        );

        response = self.client.post(
            reverse("forums:delete_message", kwargs={'message_id':message.id})
        );

        self.assertEqual(response.status_code, 302);
        self.assertTrue(response.url.startswith(reverse("accounts:login")));
        self.assertTrue(Message.objects.filter(pk=message.pk).exists());

    def test_moderator_edits_goal_forum(self):
        # o fórum de meta antes quebrava aqui (Goal não tem "community")
        self.client.force_login(self.moderator);
        url = reverse("forums:edit_forum", kwargs={'forum_id':self.goal_forum.id});

        self.assertEqual(self.client.get(url).status_code, 200);

        response = self.client.post(url, data={
            'name':'Novo nome', 'state':Forum.State.ACTIVE
        });
        self.assertEqual(response.status_code, 302);
        self.goal_forum.refresh_from_db();
        self.assertEqual(self.goal_forum.name, 'Novo nome');

    def test_edit_forum_popup_goes_back_to_next_page(self):
        # os pop-ups (comunidade e fórum) enviam "next"
        self.client.force_login(self.moderator);
        url = reverse("forums:edit_forum", kwargs={'forum_id':self.goal_forum.id});
        community_page = reverse(
            "communities:view_community", kwargs={'community_id':self.community.id}
        );

        response = self.client.post(url, data={
            'name':'Pelo popup', 'state':Forum.State.LOCKED, 'next':community_page
        });

        self.assertRedirects(response, community_page, fetch_redirect_response=False);
        self.goal_forum.refresh_from_db();
        self.assertEqual(self.goal_forum.name, 'Pelo popup');
        self.assertEqual(self.goal_forum.state, Forum.State.LOCKED);

    def test_edit_forum_ignores_external_next(self):
        self.client.force_login(self.moderator);
        url = reverse("forums:edit_forum", kwargs={'forum_id':self.goal_forum.id});

        response = self.client.post(url, data={
            'name':'Nome', 'state':Forum.State.ACTIVE, 'next':'https://evil.example/'
        });

        self.assertRedirects(response, url, fetch_redirect_response=False);

    def test_edit_forum_popup_with_invalid_data_goes_back_without_saving(self):
        self.client.force_login(self.moderator);
        url = reverse("forums:edit_forum", kwargs={'forum_id':self.goal_forum.id});
        community_page = reverse(
            "communities:view_community", kwargs={'community_id':self.community.id}
        );
        old_name = self.goal_forum.name;

        response = self.client.post(url, data={
            'name':'', 'state':Forum.State.ACTIVE, 'next':community_page
        });

        self.assertRedirects(response, community_page, fetch_redirect_response=False);
        self.goal_forum.refresh_from_db();
        self.assertEqual(self.goal_forum.name, old_name);

    def test_edit_dots_button_is_in_goal_forum_only_for_moderation(self):
        # fórum de meta: três pontinhos + pop-up; fórum geral mantém o link
        for user in (self.com_owner, self.moderator):
            self.client.force_login(user);
            response = self.client.get(self.forum_url(self.goal_forum));
            self.assertContains(response, 'id="forumEditDots"');
            self.assertContains(response, 'id="forumEditDialog"');
            self.assertContains(response, 'name="next"');

            response = self.client.get(self.forum_url(self.community_forum));
            self.assertNotContains(response, 'id="forumEditDots"');
            self.assertContains(response, 'id="forumEdit"');

        # participante comum da meta não edita
        self.client.force_login(self.goal_participant);
        response = self.client.get(self.forum_url(self.goal_forum));
        self.assertNotContains(response, 'id="forumEditDots"');
        self.assertNotContains(response, 'id="forumEditDialog"');

    def test_member_cannot_edit_forums(self):
        self.client.force_login(self.member);
        for forum in (self.community_forum, self.goal_forum):
            response = self.client.get(
                reverse("forums:edit_forum", kwargs={'forum_id':forum.id})
            );
            self.assertEqual(response.status_code, 403);

    def test_anonymous_cannot_edit_forum(self):
        response = self.client.get(
            reverse("forums:edit_forum", kwargs={'forum_id':self.community_forum.id})
        );
        self.assertEqual(response.status_code, 302);
        self.assertTrue(response.url.startswith(reverse("accounts:login")));

    def test_edit_button_is_shown_to_creator_and_moderator_only(self):
        url = reverse("forums:edit_forum", kwargs={'forum_id':self.community_forum.id});
        for user in (self.com_owner, self.moderator):
            self.client.force_login(user);
            response = self.client.get(self.forum_url(self.community_forum));
            self.assertContains(response, url);

        self.client.force_login(self.member);
        response = self.client.get(self.forum_url(self.community_forum));
        self.assertNotContains(response, url);

    def test_invalid_message_error_is_shown_to_the_user(self):
        # mensagem acima do limite: o erro precisa aparecer na página,
        # não só o recarregamento silencioso do formulário.
        self.client.force_login(self.member);
        response = self.client.post(
            self.forum_url(self.community_forum), data={'content':'x' * 5001}
        );

        self.assertEqual(response.status_code, 400);
        self.assertContains(response, 'class="form-error"', status_code=400);
        self.assertFalse(Message.objects.filter(forum=self.community_forum).exists());

    # ===== ATALHOS E PÁGINAS QUE LEVAM AO FÓRUM =====
    def test_community_forum_shortcut_redirects_to_forum(self):
        self.client.force_login(self.member);
        response = self.client.get(
            reverse("communities:forum", kwargs={'community_id':self.community.id})
        );
        self.assertRedirects(
            response, self.forum_url(self.community_forum), fetch_redirect_response=False
        );

    def test_goal_forum_shortcut_redirects_to_forum(self):
        self.client.force_login(self.goal_participant);
        response = self.client.get(
            reverse("goals:forum", kwargs={'goal_id':self.community_goal.id})
        );
        self.assertRedirects(
            response, self.forum_url(self.goal_forum), fetch_redirect_response=False
        );

    def test_goal_forum_shortcut_is_404_for_individual_goal(self):
        self.client.force_login(self.com_owner);
        response = self.client.get(
            reverse("goals:forum", kwargs={'goal_id':self.user_goal.id})
        );
        self.assertEqual(response.status_code, 404);

    def test_individual_goal_page_works_without_forum(self):
        # o dono participa da própria meta individual, que não tem fórum.
        # Antes, goal.forum levantava Forum.DoesNotExist (erro 500).
        GoalService.join(self.com_owner, self.user_goal);

        self.client.force_login(self.com_owner);
        response = self.client.get(
            reverse("goals:view_goal", kwargs={'goal_id':self.user_goal.id})
        );

        self.assertEqual(response.status_code, 200);
        self.assertIsNone(response.context['forum']);

    def test_goal_page_links_to_forum_for_participants_only(self):
        url = reverse("goals:view_goal", kwargs={'goal_id':self.community_goal.id});
        forum_link = self.forum_url(self.goal_forum);

        self.client.force_login(self.goal_participant);
        self.assertContains(self.client.get(url), forum_link);

        self.client.force_login(self.member);
        self.assertNotContains(self.client.get(url), forum_link);

    def test_goal_card_in_community_page_links_to_goal_forum(self):
        self.client.force_login(self.member);
        response = self.client.get(
            reverse("communities:view_community", kwargs={'community_id':self.community.id})
        );
        self.assertContains(response, self.forum_url(self.goal_forum));

# ---------------------------------------------------------------------------
# CT04 - criação dos fóruns
# ---------------------------------------------------------------------------
class ForumCreationRules(TestCase):
    def test_forum_name_fits_the_field_even_with_a_long_community_name(self):
        owner = AccountService.create_account(
            get_user_model().objects.create(username='Owner')
        );
        community = CommunityService.create_community(Community.objects.create(
            name='C'*100,
            creator=owner
        ));

        self.assertLessEqual(len(community.forum.name), FORUM_NAME_MAX_LENGTH);
        community.forum.clean_fields(); # o nome é válido para o formulário de edição

    def test_creating_the_community_twice_keeps_one_general_forum(self):
        owner = AccountService.create_account(
            get_user_model().objects.create(username='Owner')
        );
        community = CommunityService.create_community(Community.objects.create(
            name='NewCommunity',
            creator=owner
        ));
        CommunityService.create_community(community);

        self.assertEqual(Forum.objects.filter(community=community).count(), 1);

    def test_migration_creates_forums_that_were_missing(self):
        # comunidade e metas criadas "antigamente", sem passar pelos
        # services, ou seja, sem fórum.
        owner = AccountService.create_account(
            get_user_model().objects.create(username='Owner')
        );
        community = Community.objects.create(name='Legacy', creator=owner);
        collective = Goal.objects.create(
            name='Legacy goal', owner_community=community,
            goal_type=Goal.GoalType.PAGE_COUNT, target=10,
        );
        individual = Goal.objects.create(
            name='Legacy personal', owner_profile=owner.profile,
            goal_type=Goal.GoalType.PAGE_COUNT, target=10,
        );
        migration = importlib.import_module(
            "forums.migrations.0005_create_missing_forums"
        );

        migration.create_missing_forums(apps, None);
        migration.create_missing_forums(apps, None); # idempotente

        self.assertEqual(Forum.objects.get(community=community).name, 'Legacy Forum');
        self.assertEqual(Forum.objects.get(goal=collective).name, 'Legacy goal');
        self.assertFalse(Forum.objects.filter(goal=individual).exists());
        self.assertEqual(Forum.objects.count(), 2);