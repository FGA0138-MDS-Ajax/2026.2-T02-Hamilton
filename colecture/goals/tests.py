from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Profile
from books.models import Book
from communities.models import Community, Membership
from forums.models import Forum

from .models import Goal, GoalParticipation
from .services import GoalService

User = get_user_model()


class GoalBase(TestCase):
    def setUp(self):
        self.client = Client()
        self.creator = User.objects.create_user("creator", password="x")
        self.moderator = User.objects.create_user("moderator", password="x")
        self.member = User.objects.create_user("member", password="x")
        self.outsider = User.objects.create_user("outsider", password="x")
        for u in (self.creator, self.moderator, self.member, self.outsider):
            Profile.objects.create(user=u)

        # o criador da comunidade não possui Membership
        self.community = Community.objects.create(name="Comm", creator=self.creator)
        Membership.objects.create(
            user=self.moderator, community=self.community,
            role=Membership.Role.MODERATOR, status=Membership.Status.ACTIVE)
        Membership.objects.create(
            user=self.member, community=self.community,
            role=Membership.Role.MEMBER, status=Membership.Status.ACTIVE)
        self.book = Book.objects.create(isbn="1234567890", title="Livro", author="Autor")

        self.url_create_community = reverse(
            "goals:create_community_goal", kwargs={"community_id": self.community.id})
        self.url_create_profile = reverse("goals:create_profile_goal")

    def payload(self, **overrides):
        data = {
            "name": "Ler 1000 páginas",
            "goal_type": Goal.GoalType.PAGE_COUNT,
            "target": 1000,
            "deadline": (timezone.now() + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M"),
            "book": self.book.id,
        }
        data.update(overrides)
        return data

    def make_collective_goal(self, **kwargs):
        goal = Goal.objects.create(
            name="Coletiva", owner_community=self.community,
            goal_type=Goal.GoalType.PAGE_COUNT, target=500, **kwargs)
        Forum.objects.create(name="Coletiva", goal=goal)
        return goal


class CT04GoalCreation(GoalBase):
    def test_create_individual_goal_VALID(self):
        self.client.force_login(self.member)
        response = self.client.post(self.url_create_profile, self.payload())
        self.assertEqual(response.status_code, 302)

        goal = Goal.objects.get()
        self.assertEqual(goal.owner_profile.user, self.member)
        self.assertIsNone(goal.owner_community)
        self.assertEqual(goal.name, "Ler 1000 páginas")
        self.assertEqual(goal.target, 1000)
        self.assertEqual(goal.book, self.book)
        self.assertEqual(goal.status, Goal.Status.ACTIVE)
        self.assertFalse(Forum.objects.filter(goal=goal).exists())  # sem fórum
        self.assertTrue(GoalService.user_participates(self.member, goal))

    def test_create_collective_goal_VALID(self):
        for user in (self.moderator, self.creator):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.post(
                    self.url_create_community, self.payload(name=f"Meta {user.username}"))
                self.assertEqual(response.status_code, 302)
                goal = Goal.objects.get(name=f"Meta {user.username}")
                self.assertEqual(goal.owner_community, self.community)
                self.assertIsNone(goal.owner_profile)
                forum = Forum.objects.get(goal=goal)  # só a coletiva gera fórum
                self.assertIsNone(forum.community)

    def test_create_collective_goal_INVALID_permission(self):
        for user in (self.member, self.outsider):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.post(self.url_create_community, self.payload())
                self.assertEqual(response.status_code, 403)
        self.assertEqual(Goal.objects.count(), 0)

    def test_create_goal_INVALID_data(self):
        past = (timezone.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        invalid = [
            {"name": ""},
            {"target": 0},
            {"target": -5},
            {"target": "abc"},
            {"goal_type": "WRONG"},
            {"deadline": past},
        ]
        self.client.force_login(self.member)
        for override in invalid:
            with self.subTest(override=override):
                response = self.client.post(self.url_create_profile, self.payload(**override))
                self.assertEqual(response.status_code, 200)  # reexibe o form
        self.assertEqual(Goal.objects.count(), 0)

    def test_create_goal_without_deadline_and_book_VALID(self):
        self.client.force_login(self.member)
        data = self.payload()
        del data["deadline"], data["book"]
        self.assertEqual(self.client.post(self.url_create_profile, data).status_code, 302)
        goal = Goal.objects.get()
        self.assertIsNone(goal.deadline)
        self.assertIsNone(goal.book)

    def test_goal_with_both_owners_INVALID(self):
        base = dict(name="X", goal_type=Goal.GoalType.PAGE_COUNT, target=10)
        both = Goal(owner_community=self.community,
                    owner_profile=self.member.profile, **base)
        neither = Goal(**base)
        for goal in (both, neither):
            with self.subTest(goal=goal):
                with self.assertRaises(ValidationError):
                    goal.full_clean()
                # o banco também rejeita (CheckConstraint)
                with self.assertRaises(IntegrityError), transaction.atomic():
                    goal.save()
        self.assertEqual(Goal.objects.count(), 0)


class CT04GoalEdit(GoalBase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.member)
        self.client.post(self.url_create_profile, self.payload())
        self.personal = Goal.objects.get(owner_profile=self.member.profile)
        self.collective = self.make_collective_goal()

    def edit_url(self, goal):
        return reverse("goals:edit_goal", kwargs={"goal_id": goal.id})

    def edit_payload(self, goal, **overrides):
        # na edição o campo status é obrigatório no form
        data = {"status": goal.status}
        data.update(overrides)
        return self.payload(**data)

    def test_edit_personal_goal_by_owner_VALID(self):
        self.client.force_login(self.member)
        response = self.client.post(
            self.edit_url(self.personal),
            self.edit_payload(self.personal, name="Novo nome", target=2000,
                              status=Goal.Status.PAUSED))
        self.assertEqual(response.status_code, 302)
        self.personal.refresh_from_db()
        self.assertEqual(self.personal.name, "Novo nome")
        self.assertEqual(self.personal.target, 2000)
        self.assertEqual(self.personal.status, Goal.Status.PAUSED)

    def test_edit_collective_goal_by_moderator_VALID_and_renames_forum(self):
        self.client.force_login(self.moderator)
        response = self.client.post(
            self.edit_url(self.collective),
            self.edit_payload(self.collective, name="Renomeada"))
        self.assertEqual(response.status_code, 302)
        self.collective.refresh_from_db()
        self.assertEqual(self.collective.name, "Renomeada")
        self.assertEqual(self.collective.forum.name, "Renomeada")

    def test_edit_INVALID_permission(self):
        cases = [
            (self.outsider, self.personal),   # outro usuário, meta individual
            (self.moderator, self.personal),  # moderador não gerencia meta de perfil
            (self.member, self.collective),   # membro comum, meta coletiva
            (self.outsider, self.collective),
        ]
        for user, goal in cases:
            with self.subTest(user=user.username, goal=goal.name):
                self.client.force_login(user)
                response = self.client.post(
                    self.edit_url(goal), self.edit_payload(goal, name="Hackeada"))
                self.assertEqual(response.status_code, 403)
                goal.refresh_from_db()
                self.assertNotEqual(goal.name, "Hackeada")

    def test_edit_INVALID_data(self):
        self.client.force_login(self.member)
        for override in ({"name": ""}, {"target": 0}, {"goal_type": "WRONG"},
                         {"status": "WRONG"}):
            with self.subTest(override=override):
                response = self.client.post(
                    self.edit_url(self.personal), self.edit_payload(self.personal, **override))
                self.assertEqual(response.status_code, 200)
        self.personal.refresh_from_db()
        self.assertEqual(self.personal.target, 1000)

    def test_edit_cannot_change_owner(self):
        self.client.force_login(self.member)
        self.client.post(self.edit_url(self.personal), self.edit_payload(
            self.personal, owner_community=self.community.id,
            owner_profile=self.outsider.profile.id))
        self.personal.refresh_from_db()
        self.assertIsNone(self.personal.owner_community)
        self.assertEqual(self.personal.owner_profile.user, self.member)


class CT04GoalParticipation(GoalBase):
    def setUp(self):
        super().setUp()
        self.goal = self.make_collective_goal()
        self.url_join = reverse("goals:join_goal", kwargs={"goal_id": self.goal.id})
        self.url_leave = reverse("goals:leave_goal", kwargs={"goal_id": self.goal.id})

    def participation(self, user=None):
        return GoalParticipation.objects.get(goal=self.goal, user=user or self.member)

    def test_join_and_rejoin(self):
        self.client.force_login(self.member)
        self.client.post(self.url_join)
        self.assertEqual(self.participation().state, GoalParticipation.State.ACTIVE)

        self.client.post(self.url_leave)
        self.assertEqual(self.participation().state, GoalParticipation.State.INACTIVE)

        self.client.post(self.url_join)  # reinscrição reativa a mesma linha
        self.assertEqual(self.participation().state, GoalParticipation.State.ACTIVE)
        self.assertEqual(GoalParticipation.objects.filter(
            goal=self.goal, user=self.member).count(), 1)

    def test_join_twice_is_idempotent(self):
        self.client.force_login(self.member)
        self.client.post(self.url_join)
        self.client.post(self.url_join)
        self.assertEqual(GoalParticipation.objects.filter(goal=self.goal).count(), 1)

    def test_creator_without_membership_can_join(self):
        # o criador da comunidade não tem Membership, mas é da comunidade
        self.client.force_login(self.creator)
        self.client.post(self.url_join)
        self.assertEqual(self.participation(self.creator).state, GoalParticipation.State.ACTIVE)

    def test_join_collective_goal_without_membership_INVALID(self):
        with self.assertRaises(ValidationError):
            GoalService.join(self.outsider, self.goal)
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.post(self.url_join).status_code, 403)
        self.assertFalse(GoalParticipation.objects.filter(user=self.outsider).exists())

    def test_join_after_leaving_community_INVALID(self):
        membership = Membership.objects.get(user=self.member, community=self.community)
        membership.status = Membership.Status.LEFT
        membership.save()
        with self.assertRaises(ValidationError):
            GoalService.join(self.member, self.goal)

    def test_join_paused_or_concluded_goal_INVALID(self):
        self.client.force_login(self.member)
        for status in (Goal.Status.PAUSED, Goal.Status.CONCLUDED):
            with self.subTest(status=status):
                self.goal.status = status
                self.goal.save()
                with self.assertRaises(ValidationError):
                    GoalService.join(self.member, self.goal)
                self.client.post(self.url_join)
                self.assertFalse(GoalParticipation.objects.filter(
                    goal=self.goal, user=self.member).exists())

    def test_leave_goal_deactivates_participation(self):
        GoalService.join(self.member, self.goal)
        self.client.force_login(self.member)
        self.client.post(self.url_leave)
        self.assertEqual(self.participation().state, GoalParticipation.State.INACTIVE)

    def test_leave_community_voluntarily_deactivates_participation(self):
        GoalService.join(self.member, self.goal)
        self.client.force_login(self.member)
        self.client.post(reverse("communities:leave_community",
                                 kwargs={"community_id": self.community.id}))
        self.assertEqual(self.participation().state, GoalParticipation.State.INACTIVE)

    def test_forced_leave_community_deactivates_participation(self):
        GoalService.join(self.member, self.goal)
        membership = Membership.objects.get(user=self.member, community=self.community)
        membership.status = Membership.Status.BANNED
        membership.save()
        self.assertEqual(self.participation().state, GoalParticipation.State.INACTIVE)

    def test_creator_leaving_community_deactivates_participation(self):
        GoalService.join(self.creator, self.goal)
        self.client.force_login(self.creator)
        self.client.post(reverse("communities:leave_community",
                                 kwargs={"community_id": self.community.id}))
        self.assertEqual(self.participation(self.creator).state,
                         GoalParticipation.State.INACTIVE)

    def test_other_communities_participation_untouched(self):
        other = Community.objects.create(name="Other", creator=self.creator)
        Membership.objects.create(user=self.member, community=other,
                                  role=Membership.Role.MEMBER, status=Membership.Status.ACTIVE)
        other_goal = Goal.objects.create(
            name="Outra", owner_community=other,
            goal_type=Goal.GoalType.PAGE_COUNT, target=10)
        GoalService.join(self.member, other_goal)

        membership = Membership.objects.get(user=self.member, community=self.community)
        membership.status = Membership.Status.LEFT
        membership.save()
        self.assertEqual(GoalParticipation.objects.get(goal=other_goal, user=self.member).state,
                         GoalParticipation.State.ACTIVE)
