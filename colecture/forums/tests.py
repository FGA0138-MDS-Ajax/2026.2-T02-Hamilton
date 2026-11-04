from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model;
from .models import Forum, Message

from communities.models import Community;
from communities.services import CommunityService, MembershipService;
from goals.models import Goal, GoalParticipation;
from goals.services import GoalService;
from accounts.services import AccountService;

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

        cls.community_forum = cls.community.forum;
        cls.goal_forum = cls.community_goal.forum;

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