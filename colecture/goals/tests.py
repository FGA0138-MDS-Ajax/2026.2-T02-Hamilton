import json
from datetime import timedelta, date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Profile
from books.models import Book, BookStatus, ReadingSession
from communities.models import Community, Membership
from forums.models import Forum

from .models import GOAL_DESC_MAX_LENGTH, Goal, GoalParticipation
from .forms import GoalForm
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

    def set_community_book(self, **kwargs):
        """Define um livro para a comunidade (por padrão ela não tem livro)."""
        community_book = Book.objects.create(
            isbn="9876543210", title="Livro da comunidade", author="Autor 2", **kwargs)
        self.community.book = community_book
        self.community.save()
        return community_book

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
        # o prazo é só a data (vale até o fim do dia), então "passado" é ontem
        past = (timezone.localdate() - timedelta(days=1)).strftime("%Y-%m-%d")
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

    def test_page_goal_limited_to_community_book_pages(self):
        self.set_community_book(pages=200)
        self.client.force_login(self.moderator)
        for target, created in ((201, False), (200, True)):
            with self.subTest(target=target):
                self.client.post(self.url_create_community,
                                 self.payload(name=f"Meta {target}", target=target))
                self.assertEqual(Goal.objects.filter(name=f"Meta {target}").exists(), created)

    def test_page_goal_limited_to_individual_book_pages(self):
        self.book.pages = 300
        self.book.save()
        self.client.force_login(self.member)
        response = self.client.post(self.url_create_profile, self.payload(target=301))
        self.assertEqual(response.status_code, 200)  # reexibe o form
        self.assertContains(response, "tem 300 páginas")
        self.assertEqual(Goal.objects.count(), 0)

    def test_page_goal_without_book_pages_has_general_cap(self):
        # livro antigo, cadastrado sem nº de páginas: vale o teto geral
        self.client.force_login(self.member)
        self.client.post(self.url_create_profile, self.payload(target=50_000_000_000))
        self.assertEqual(Goal.objects.count(), 0)

    def test_hour_goal_target_saved_in_minutes(self):
        self.client.force_login(self.member)
        response = self.client.post(self.url_create_profile, self.payload(
            goal_type=Goal.GoalType.HOUR_COUNT, target="", target_time="1:30"))
        self.assertEqual(response.status_code, 302)
        goal = Goal.objects.get()
        self.assertEqual(goal.target, 90)
        self.assertEqual(goal.target_display, "1h30")

    def test_create_goal_without_deadline_and_book_VALID(self):
        self.client.force_login(self.member)
        data = self.payload()
        del data["deadline"], data["book"]
        self.assertEqual(self.client.post(self.url_create_profile, data).status_code, 302)
        goal = Goal.objects.get()
        self.assertIsNone(goal.deadline)
        self.assertIsNone(goal.book)

    def test_create_collective_goal_uses_community_book_VALID(self):
        community_book = self.set_community_book()
        self.client.force_login(self.moderator)
        # o payload traz outro livro (self.book); o campo foi removido do
        # form de meta de comunidade, então deve ser ignorado
        response = self.client.post(self.url_create_community, self.payload())
        self.assertEqual(response.status_code, 302)
        goal = Goal.objects.get(owner_community=self.community)
        self.assertEqual(goal.book, community_book)

    def test_goal_form_book_field_only_for_individual_goal(self):
        collective = GoalForm(instance=Goal(owner_community=self.community))
        individual = GoalForm(instance=Goal(owner_profile=self.member.profile))
        self.assertNotIn("book", collective.fields)
        self.assertIn("book", individual.fields)

    def test_goal_form_labels_are_in_portuguese(self):
        form = GoalForm(instance=Goal(owner_profile=self.member.profile))
        labels = {name: field.label for name, field in form.fields.items()}
        self.assertEqual(labels, {
            "name": "Nome da meta",
            "description": "Descrição",
            "goal_type": "Tipo de meta",
            "target": "Quantidade-alvo",
            "deadline": "Prazo",
            "book": "Livro",
            "target_time": "Tempo de leitura",
        })
        # a primeira opção é o texto em branco do Django (varia por versão)
        self.assertEqual(
            [label for _, label in list(form.fields["goal_type"].choices)[1:]],
            ["Páginas", "Horas"],
        )

    def test_create_goal_with_description_VALID(self):
        self.client.force_login(self.member)
        response = self.client.post(
            self.url_create_profile, self.payload(description="Um capítulo por dia"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Goal.objects.get().description, "Um capítulo por dia")

    def test_create_goal_without_description_VALID(self):
        self.client.force_login(self.member)
        self.assertEqual(
            self.client.post(self.url_create_profile, self.payload()).status_code, 302)
        self.assertEqual(Goal.objects.get().description, "")

    def test_create_goal_INVALID_description_too_long(self):
        self.client.force_login(self.member)
        response = self.client.post(
            self.url_create_profile,
            self.payload(description="a" * (GOAL_DESC_MAX_LENGTH + 1)))
        self.assertEqual(response.status_code, 200)  # reexibe o form
        self.assertEqual(Goal.objects.count(), 0)

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

    def test_edit_collective_goal_keeps_its_book_VALID(self):
        # a meta nasceu com self.book; depois a comunidade troca de livro
        goal = self.make_collective_goal(book=self.book)
        self.set_community_book()
        self.client.force_login(self.moderator)
        response = self.client.post(
            self.edit_url(goal),
            self.edit_payload(goal, name="Renomeada", description="Nova descrição"))
        self.assertEqual(response.status_code, 302)
        goal.refresh_from_db()
        self.assertEqual(goal.book, self.book)
        self.assertEqual(goal.description, "Nova descrição")

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


class CT04GoalAutoParticipation(GoalBase):
    """Metas de comunidade inscrevem os membros automaticamente."""

    def create_goal_via_view(self, user, **overrides):
        self.client.force_login(user)
        response = self.client.post(
            self.url_create_community, self.payload(name="Automática", **overrides))
        self.assertEqual(response.status_code, 302)
        return Goal.objects.get(name="Automática")

    def active_users(self, goal):
        return set(GoalParticipation.objects.filter(
            goal=goal, state=GoalParticipation.State.ACTIVE
        ).values_list("user__username", flat=True))

    def add_member(self, username, status=Membership.Status.ACTIVE,
                   role=Membership.Role.MEMBER):
        user = User.objects.create_user(username, password="x")
        Profile.objects.create(user=user)
        Membership.objects.create(
            user=user, community=self.community, role=role, status=status)
        return user

    # ---------- criação da meta ----------
    def test_new_goal_enrolls_every_active_member_and_the_creator_VALID(self):
        goal = self.create_goal_via_view(self.moderator)
        self.assertEqual(
            self.active_users(goal), {"creator", "moderator", "member"})

    def test_new_goal_enrolls_members_when_created_by_the_community_creator_VALID(self):
        goal = self.create_goal_via_view(self.creator)
        self.assertEqual(
            self.active_users(goal), {"creator", "moderator", "member"})

    def test_new_goal_skips_non_active_members_and_outsiders_INVALID(self):
        self.add_member("pending", status=Membership.Status.PENDING,
                        role=Membership.Role.NONE)
        self.add_member("left", status=Membership.Status.LEFT)
        self.add_member("banned", status=Membership.Status.BANNED)
        goal = self.create_goal_via_view(self.moderator)
        users = self.active_users(goal)
        self.assertNotIn("pending", users)
        self.assertNotIn("left", users)
        self.assertNotIn("banned", users)
        self.assertNotIn("outsider", users)

    def test_new_goal_has_one_participation_per_member_VALID(self):
        goal = self.create_goal_via_view(self.moderator)
        # o moderador que criou a meta não é inscrito duas vezes
        self.assertEqual(goal.participations.count(), 3)

    def test_individual_goal_enrolls_only_its_owner_VALID(self):
        self.client.force_login(self.member)
        self.client.post(self.url_create_profile, self.payload())
        goal = Goal.objects.get(owner_profile=self.member.profile)
        self.assertEqual(self.active_users(goal), {"member"})

    def test_join_all_members_ignores_goals_that_are_not_active_INVALID(self):
        for status in (Goal.Status.PAUSED, Goal.Status.CONCLUDED):
            with self.subTest(status=status):
                goal = Goal.objects.create(
                    name=f"Meta {status}", owner_community=self.community,
                    goal_type=Goal.GoalType.PAGE_COUNT, target=10, status=status)
                self.assertEqual(GoalService.join_all_members(goal), 0)
                self.assertFalse(goal.participations.exists())

    def test_join_all_members_keeps_who_left_the_goal_VALID(self):
        goal = self.make_collective_goal()
        GoalService.join_all_members(goal)
        GoalService.leave(self.member, goal)
        self.assertEqual(GoalService.join_all_members(goal), 0)
        self.assertEqual(
            GoalParticipation.objects.get(goal=goal, user=self.member).state,
            GoalParticipation.State.INACTIVE)

    def test_goal_of_archived_community_enrolls_nobody_INVALID(self):
        self.community.state = Community.State.ARCHIVED
        self.community.save()
        goal = self.make_collective_goal()
        self.assertEqual(GoalService.join_all_members(goal), 0)

    # ---------- entrada na comunidade com meta ativa ----------
    def test_new_member_joins_active_goals_automatically_VALID(self):
        goal = self.make_collective_goal()
        newcomer = self.add_member("newcomer")
        self.assertIn("newcomer", self.active_users(goal))
        self.assertTrue(GoalService.user_participates(newcomer, goal))

    def test_joining_through_the_view_enrolls_in_the_goal_VALID(self):
        goal = self.make_collective_goal()
        self.client.force_login(self.outsider)
        self.client.post(reverse(
            "communities:join_community", kwargs={"community_id": self.community.id}))
        self.assertIn("outsider", self.active_users(goal))

    def test_new_member_joins_every_active_goal_of_the_community_VALID(self):
        first = self.make_collective_goal()
        second = Goal.objects.create(
            name="Segunda", owner_community=self.community,
            goal_type=Goal.GoalType.HOUR_COUNT, target=5)
        self.add_member("newcomer")
        self.assertIn("newcomer", self.active_users(first))
        self.assertIn("newcomer", self.active_users(second))

    def test_new_member_does_not_join_paused_or_concluded_goals_INVALID(self):
        paused = self.make_collective_goal(status=Goal.Status.PAUSED)
        concluded = self.make_collective_goal(status=Goal.Status.CONCLUDED)
        newcomer = self.add_member("newcomer")
        for goal in (paused, concluded):
            self.assertFalse(GoalParticipation.objects.filter(
                goal=goal, user=newcomer).exists())

    def test_new_member_does_not_join_goals_of_other_communities_INVALID(self):
        other = Community.objects.create(name="Other", creator=self.creator)
        other_goal = Goal.objects.create(
            name="Outra", owner_community=other,
            goal_type=Goal.GoalType.PAGE_COUNT, target=10)
        self.make_collective_goal()
        newcomer = self.add_member("newcomer")
        self.assertFalse(GoalParticipation.objects.filter(
            goal=other_goal, user=newcomer).exists())

    def test_pending_request_joins_the_goal_only_after_approval_VALID(self):
        goal = self.make_collective_goal()
        applicant = self.add_member(
            "applicant", status=Membership.Status.PENDING, role=Membership.Role.NONE)
        self.assertNotIn("applicant", self.active_users(goal))

        membership = Membership.objects.get(user=applicant, community=self.community)
        self.client.force_login(self.moderator)
        self.client.post(
            reverse("communities:manage_membership_request", kwargs={
                "community_id": self.community.id, "membership_id": membership.id}),
            {"decision": "accept"})
        self.assertIn("applicant", self.active_users(goal))

    def test_rejected_request_does_not_join_the_goal_INVALID(self):
        goal = self.make_collective_goal()
        applicant = self.add_member(
            "applicant", status=Membership.Status.PENDING, role=Membership.Role.NONE)
        membership = Membership.objects.get(user=applicant, community=self.community)
        self.client.force_login(self.moderator)
        self.client.post(
            reverse("communities:manage_membership_request", kwargs={
                "community_id": self.community.id, "membership_id": membership.id}),
            {"decision": "reject"})
        self.assertNotIn("applicant", self.active_users(goal))

    def test_returning_to_the_community_reactivates_participation_VALID(self):
        goal = self.make_collective_goal()
        GoalService.join(self.member, goal)
        membership = Membership.objects.get(user=self.member, community=self.community)
        membership.status = Membership.Status.LEFT
        membership.save()
        self.assertNotIn("member", self.active_users(goal))

        membership.status = Membership.Status.ACTIVE
        membership.save()
        self.assertIn("member", self.active_users(goal))
        self.assertEqual(GoalParticipation.objects.filter(
            goal=goal, user=self.member).count(), 1)

    def test_changing_role_does_not_reenroll_who_left_the_goal_VALID(self):
        goal = self.make_collective_goal()
        GoalService.join(self.member, goal)
        GoalService.leave(self.member, goal)

        membership = Membership.objects.get(user=self.member, community=self.community)
        membership.role = Membership.Role.MODERATOR
        membership.save()
        self.assertNotIn("member", self.active_users(goal))


class CT_GoalConclude(GoalBase):
    """F11: marcar a meta como concluída."""

    def setUp(self):
        super().setUp()
        self.goal = self.make_collective_goal()
        self.url = reverse("goals:conclude_goal", kwargs={"goal_id": self.goal.id})

    def test_moderator_concludes_goal_VALID(self):
        self.client.force_login(self.moderator)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.status, Goal.Status.CONCLUDED)

    def test_common_member_cannot_conclude_INVALID(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.post(self.url).status_code, 403)
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.status, Goal.Status.ACTIVE)

    def test_conclude_requires_post_INVALID(self):
        self.client.force_login(self.moderator)
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_conclude_goes_back_to_next_only_when_it_is_local(self):
        self.client.force_login(self.moderator)
        response = self.client.post(self.url, {"next": "/communities/1"})
        self.assertEqual(response["Location"], "/communities/1")

        self.goal.status = Goal.Status.ACTIVE
        self.goal.save()
        response = self.client.post(self.url, {"next": "https://evil.example/"})
        self.assertEqual(
            response["Location"],
            reverse("communities:view_community", kwargs={"community_id": self.goal.owner_community_id}))


# Testes dos métodos de ofensiva do Profile (sem requisição HTTP)
class ProfileStreakModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="leitor", password="senha123")
        self.profile = Profile.objects.create(user=self.user)
        self.today = date(2026, 11, 7)

    def test_primeira_leitura_inicia_ofensiva_em_1(self):
        changed = self.profile.register_reading_day(self.today, today=self.today)

        self.assertTrue(changed)
        self.assertEqual(self.profile.streak, 1)
        self.assertEqual(self.profile.last_read_date, self.today)

    def test_dias_consecutivos_incrementam_ofensiva(self):
        for offset in (2, 1, 0):
            self.profile.register_reading_day(
                self.today - timedelta(days=offset), today=self.today)

        self.assertEqual(self.profile.streak, 3)

    def test_mesmo_dia_nao_incrementa_duas_vezes(self):
        self.profile.register_reading_day(self.today, today=self.today)
        changed = self.profile.register_reading_day(self.today, today=self.today)

        self.assertFalse(changed)
        self.assertEqual(self.profile.streak, 1)

    def test_leitura_retroativa_nao_altera_ofensiva(self):
        self.profile.streak = 3
        self.profile.last_read_date = self.today

        changed = self.profile.register_reading_day(
            self.today - timedelta(days=1), today=self.today)

        self.assertFalse(changed)
        self.assertEqual(self.profile.streak, 3)
        self.assertEqual(self.profile.last_read_date, self.today)

    def test_faltar_um_dia_reseta_ofensiva_para_zero(self):
        self.profile.streak = 5
        self.profile.last_read_date = self.today - timedelta(days=2)

        reset = self.profile.reset_streak_if_broken(today=self.today)

        self.assertTrue(reset)
        self.assertEqual(self.profile.streak, 0)

    def test_ofensiva_de_ontem_continua_viva(self):
        self.profile.streak = 5
        self.profile.last_read_date = self.today - timedelta(days=1)

        self.assertFalse(self.profile.reset_streak_if_broken(today=self.today))
        self.assertEqual(self.profile.streak, 5)

    def test_ler_depois_de_faltar_recomeca_em_1(self):
        self.profile.streak = 5
        self.profile.last_read_date = self.today - timedelta(days=3)

        self.profile.register_reading_day(self.today, today=self.today)

        self.assertEqual(self.profile.streak, 1)
        self.assertEqual(self.profile.last_read_date, self.today)

    def test_data_futura_levanta_erro_e_nao_altera(self):
        with self.assertRaises(ValueError):
            self.profile.register_reading_day(
                self.today + timedelta(days=1), today=self.today)

        self.assertEqual(self.profile.streak, 0)
        self.assertIsNone(self.profile.last_read_date)

    def test_ofensiva_negativa_e_invalida(self):
        self.profile.streak = -1

        with self.assertRaises(ValidationError):
            self.profile.full_clean()




# ---------------------------------------------------------------------------
# Fase 2: metas após criar/editar sessões pelos endpoints JSON
# ---------------------------------------------------------------------------
class GoalReadingSessionApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("meta_leitor", password="x")
        self.other = User.objects.create_user("meta_outro", password="x")
        self.profile = Profile.objects.create(user=self.user)
        self.other_profile = Profile.objects.create(user=self.other)
        self.book = Book.objects.create(isbn="9780590353403", title="Com páginas", author="A", pages=100)
        self.book_no_pages = Book.objects.create(isbn="9780261103573", title="Sem total", author="A", pages=None)
        self.client.force_login(self.user)

    def make_goal(self, goal_type, target=500, profile=None, **kwargs):
        profile = profile or self.profile
        goal = Goal.objects.create(
            name="Meta", owner_profile=profile, goal_type=goal_type, target=target, **kwargs)
        participation = GoalParticipation.objects.create(
            user=profile.user, goal=goal, joined_at=timezone.now() - timedelta(days=30))
        # created_at é auto_now_add (hoje) e o progresso individual ignora sessões anteriores à
        # criação da meta: recua a criação junto com a entrada para aceitar sessões retroativas
        Goal.objects.filter(pk=goal.pk).update(created_at=timezone.now() - timedelta(days=30))
        goal.refresh_from_db()
        return goal, participation

    def post(self, url, payload):
        return self.client.post(url, data=json.dumps(payload), content_type="application/json")

    def create(self, book=None, **payload):
        book = book or self.book
        if "pages" in payload:  # atalho: pages=N -> pages_read=N
            payload["pages_read"] = payload.pop("pages")
        payload.setdefault("minute_count", 10)
        response = self.post(reverse("books:save_reading_session", args=[book.id]), payload)
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()["session"]["id"]

    def edit(self, session_id, book=None, **payload):
        book = book or self.book
        return self.post(reverse("books:edit_reading_session", args=[book.id, session_id]), payload)

    def when(self, days):
        base = timezone.localtime().replace(hour=12, minute=0, second=0, microsecond=0)
        return (base - timedelta(days=days)).isoformat()

    def pages(self, goal, participation):
        return (
            GoalService.get_user_contribution(participation),
            GoalService.get_individual_progress(goal)["current"],
        )

    def test_meta_de_paginas_reflete_criacao_e_edicao_com_cascata(self):
        goal, participation = self.make_goal(Goal.GoalType.PAGE_COUNT, book=self.book)
        self.create(pages=10, created_at=self.when(2))
        second = self.create(pages=20, created_at=self.when(1))
        self.assertEqual(self.pages(goal, participation), (30, 30))

        self.assertEqual(self.edit(second, pages_read=35).status_code, 200)

        self.assertEqual(self.pages(goal, participation), (45, 45))

    def test_meta_de_horas_reflete_edicao_do_tempo(self):
        goal, participation = self.make_goal(Goal.GoalType.HOUR_COUNT, target=600, book=self.book)
        session_id = self.create(pages=10, minute_count=30)
        self.create(pages=5, minute_count=15)
        self.assertEqual(self.pages(goal, participation), (45, 45))

        self.assertEqual(self.edit(session_id, minute_count=90).status_code, 200)

        self.assertEqual(self.pages(goal, participation), (105, 105))

    def test_mover_sessao_para_antes_da_entrada_na_meta_remove_a_contribuicao(self):
        goal, participation = self.make_goal(Goal.GoalType.PAGE_COUNT, book=self.book)
        participation.joined_at = timezone.now() - timedelta(days=1)
        participation.save()
        session_id = self.create(pages=12)
        self.assertEqual(GoalService.get_user_contribution(participation), 12)

        self.edit(session_id, created_at=self.when(5))

        self.assertEqual(GoalService.get_user_contribution(participation), 0)

    def test_sessao_em_percentual_conta_horas_mas_nao_paginas(self):
        pages_goal, pages_part = self.make_goal(Goal.GoalType.PAGE_COUNT, book=self.book_no_pages)
        hours_goal, hours_part = self.make_goal(Goal.GoalType.HOUR_COUNT, target=600, book=self.book_no_pages)
        session_id = self.create(book=self.book_no_pages, stopped_percent=40, minute_count=25)

        self.assertEqual(self.pages(pages_goal, pages_part), (0, 0))
        self.assertEqual(self.pages(hours_goal, hours_part), (25, 25))

        self.edit(session_id, book=self.book_no_pages, minute_count=50)
        self.assertEqual(self.pages(hours_goal, hours_part), (50, 50))

    def test_metas_de_um_usuario_nao_sao_afetadas_por_sessoes_de_outro(self):
        goal, participation = self.make_goal(Goal.GoalType.PAGE_COUNT, book=self.book)
        other_goal, other_participation = self.make_goal(
            Goal.GoalType.PAGE_COUNT, profile=self.other_profile, book=self.book)
        mine = self.create(pages=10)

        self.client.force_login(self.other)
        theirs = self.create(pages=40)
        # outro usuário não consegue editar a minha sessão
        self.assertEqual(self.edit(mine, pages_read=99).status_code, 404)
        self.assertEqual(self.edit(theirs, pages_read=50).status_code, 200)

        self.assertEqual(self.pages(goal, participation), (10, 10))
        self.assertEqual(self.pages(other_goal, other_participation), (50, 50))