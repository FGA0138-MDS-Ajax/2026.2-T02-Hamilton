from django.test import TestCase, Client
from django.contrib.auth import get_user_model;
from .models import Forum

from communities.models import Community;
from communities.services import CommunityService;
from goals.models import Goal, GoalParticipation;
from goals.services import GoalService;
from accounts.services import AccountService;

# Create your tests here.
class CT04(TestCase):
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
