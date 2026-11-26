import json
from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.services import AccountService
from communities.models import Community, Membership
from communities.services import CommunityService, MembershipService
from forums.models import Message
from logs.models import AuditLog
from logs.services import create_log


def make_user(username, superuser=False):
    """Cria um usuário já com Profile (como o cadastro faz)."""
    manager = get_user_model().objects.create_superuser if superuser else (
        get_user_model().objects.create
    )
    return AccountService.create_account(manager(username=username))


# ---------------------------------------------------------------------------
# Serviço de registro (create_log)
# ---------------------------------------------------------------------------
class AuditLogServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = make_user('Owner')
        cls.community = CommunityService.create_community(
            Community.objects.create(name='NewCommunity', creator=cls.owner)
        )

    def test_create_log_stores_class_and_id_of_the_target(self):
        log = create_log(
            self.owner,
            AuditLog.Action.MEMBER_ADDED,
            self.community,
            metadata={'community_id': self.community.id},
        )

        log.refresh_from_db()
        self.assertEqual(log.actor, self.owner)
        self.assertEqual(log.action, AuditLog.Action.MEMBER_ADDED)
        self.assertEqual(
            log.content_type,
            ContentType.objects.get_for_model(Community),
        )
        self.assertEqual(log.object_id, self.community.id)
        self.assertEqual(log.metadata, {'community_id': self.community.id})
        self.assertIsNotNone(log.created_at)
        self.assertEqual(log.get_target(), self.community)

    def test_metadata_defaults_to_empty_dict(self):
        log = create_log(self.owner, AuditLog.Action.MEMBER_ADDED, self.owner)
        self.assertEqual(log.metadata, {})

    def test_log_survives_deletion_of_the_target(self):
        log = create_log(
            self.owner, AuditLog.Action.COMMUNITY_DELETED, self.community
        )
        community_id = self.community.id

        self.community.delete()

        log.refresh_from_db()
        self.assertEqual(log.object_id, community_id)
        self.assertIsNone(log.get_target())

    def test_log_survives_deletion_of_the_actor(self):
        actor = make_user('Temporary')
        log = create_log(actor, AuditLog.Action.MEMBER_ADDED, self.owner)

        actor.delete()

        log.refresh_from_db()
        self.assertIsNone(log.actor)

    def test_system_action_has_no_actor(self):
        log = create_log(None, AuditLog.Action.COMMUNITY_DELETED, self.community)
        self.assertIsNone(log.actor)


# ---------------------------------------------------------------------------
# Acesso: só administradores visualizam, editam e excluem logs
# ---------------------------------------------------------------------------
class AuditLogAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = make_user('SiteAdmin', superuser=True)
        cls.reader = make_user('Reader')
        cls.owner = make_user('Owner')
        cls.community = CommunityService.create_community(
            Community.objects.create(name='NewCommunity', creator=cls.owner)
        )
        cls.log = create_log(
            cls.owner,
            AuditLog.Action.MEMBER_ADDED,
            cls.reader,
            metadata={'community_id': cls.community.id},
        )

    def setUp(self):
        self.client = Client()

    def edit_data(self):
        return {
            'actor': self.owner.id,
            'action': AuditLog.Action.MEMBER_BANNED,
            'content_type': self.log.content_type_id,
            'object_id': self.log.object_id,
            'metadata': json.dumps({'changed': True}),
        }

    def requests(self):
        """(nome, método, url, dados) de cada rota protegida."""
        args = [self.log.id]
        return [
            ('list', 'get', reverse('logs:log_list'), None),
            ('detail', 'get', reverse('logs:log_detail', args=args), None),
            ('edit GET', 'get', reverse('logs:edit_log', args=args), None),
            ('edit POST', 'post', reverse('logs:edit_log', args=args), self.edit_data()),
            ('delete POST', 'post', reverse('logs:delete_log', args=args), {}),
        ]

    def send(self, method, url, data):
        return self.client.get(url) if method == 'get' else self.client.post(url, data)

    def assert_log_untouched(self):
        self.log.refresh_from_db()
        self.assertEqual(self.log.action, AuditLog.Action.MEMBER_ADDED)
        self.assertFalse(
            AuditLog.objects.filter(action__in=[
                AuditLog.Action.LOG_EDITED,
                AuditLog.Action.LOG_DELETED,
            ]).exists()
        )

    def test_anonymous_is_sent_to_login(self):
        for name, method, url, data in self.requests():
            with self.subTest(name):
                response = self.send(method, url, data)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('accounts:login'), response.url)
        self.assert_log_untouched()

    def test_regular_reader_is_forbidden(self):
        self.client.force_login(self.reader)
        for name, method, url, data in self.requests():
            with self.subTest(name):
                response = self.send(method, url, data)
                self.assertEqual(response.status_code, 403)
        self.assert_log_untouched()

    def test_community_creator_is_not_a_site_admin(self):
        # ser criador/moderador de uma comunidade não dá acesso aos logs
        self.client.force_login(self.owner)
        for name, method, url, data in self.requests():
            with self.subTest(name):
                response = self.send(method, url, data)
                self.assertEqual(response.status_code, 403)
        self.assert_log_untouched()

    def test_admin_can_access_every_page(self):
        self.client.force_login(self.admin)
        for name, method, url, data in self.requests()[:3]:
            with self.subTest(name):
                self.assertEqual(self.send(method, url, data).status_code, 200)


# ---------------------------------------------------------------------------
# Visualização, edição e exclusão feitas por administradores
# ---------------------------------------------------------------------------
class AuditLogAdminViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = make_user('SiteAdmin', superuser=True)
        cls.reader = make_user('Reader')
        cls.owner = make_user('Owner')
        cls.log = create_log(
            cls.owner,
            AuditLog.Action.MEMBER_ADDED,
            cls.reader,
            metadata={'community_id': 7},
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.admin)

    def edit_url(self):
        return reverse('logs:edit_log', args=[self.log.id])

    def edit_data(self, **overrides):
        data = {
            'actor': self.owner.id,
            'action': AuditLog.Action.MEMBER_ADDED,
            'content_type': self.log.content_type_id,
            'object_id': self.log.object_id,
            'metadata': json.dumps({'community_id': 7}),
        }
        data.update(overrides)
        return data

    # ===== VISUALIZAR =====
    def test_list_shows_logs(self):
        response = self.client.get(reverse('logs:log_list'))

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.log, response.context['page'])

    def test_list_filters_by_action_actor_and_object(self):
        other = create_log(
            self.admin, AuditLog.Action.MESSAGE_DELETED, self.owner
        )
        url = reverse('logs:log_list')

        by_action = self.client.get(url, {'action': AuditLog.Action.MESSAGE_DELETED})
        self.assertEqual(list(by_action.context['page']), [other])

        by_actor = self.client.get(url, {'actor': 'owner'})
        self.assertEqual(list(by_actor.context['page']), [self.log])

        by_object = self.client.get(url, {'object_id': self.reader.id})
        self.assertEqual(list(by_object.context['page']), [self.log])

    def test_list_filters_by_category(self):
        msg_log = create_log(
            self.admin, AuditLog.Action.MESSAGE_DELETED, self.owner
        )
        url = reverse('logs:log_list')

        by_cat_forums = self.client.get(url, {'category': 'forums'})
        self.assertEqual(list(by_cat_forums.context['page']), [msg_log])

        by_cat_members = self.client.get(url, {'category': 'members'})
        self.assertIn(self.log, by_cat_members.context['page'])
        self.assertNotIn(msg_log, by_cat_members.context['page'])

    def test_log_category_property(self):
        msg_log = create_log(self.admin, AuditLog.Action.MESSAGE_DELETED, self.owner)
        self.assertEqual(msg_log.category, "Fóruns")
        self.assertEqual(self.log.category, "Membros")

    def test_invalid_filter_shows_no_logs(self):
        response = self.client.get(reverse('logs:log_list'), {'object_id': 'abc'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['page']), [])

    def test_detail_shows_metadata(self):
        response = self.client.get(reverse('logs:log_detail', args=[self.log.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'community_id')

    def test_detail_of_missing_log_is_404(self):
        response = self.client.get(reverse('logs:log_detail', args=[999999]))
        self.assertEqual(response.status_code, 404)

    # ===== EDITAR =====
    def test_edit_updates_the_log_and_logs_the_edit(self):
        response = self.client.post(self.edit_url(), self.edit_data(
            action=AuditLog.Action.MEMBER_BANNED,
            metadata=json.dumps({'community_id': 8}),
        ))

        self.assertEqual(response.status_code, 302)
        self.log.refresh_from_db()
        self.assertEqual(self.log.action, AuditLog.Action.MEMBER_BANNED)
        self.assertEqual(self.log.metadata, {'community_id': 8})

        edit_log = AuditLog.objects.get(action=AuditLog.Action.LOG_EDITED)
        self.assertEqual(edit_log.actor, self.admin)
        self.assertEqual(
            edit_log.content_type, ContentType.objects.get_for_model(AuditLog)
        )
        self.assertEqual(edit_log.object_id, self.log.id)
        changes = edit_log.metadata['changes']
        self.assertEqual(set(changes), {'action', 'metadata'})
        self.assertEqual(changes['action'], {
            'old': AuditLog.Action.MEMBER_ADDED,
            'new': AuditLog.Action.MEMBER_BANNED,
        })
        self.assertEqual(changes['metadata'], {
            'old': {'community_id': 7},
            'new': {'community_id': 8},
        })

    def test_edit_without_changes_does_not_log(self):
        response = self.client.post(self.edit_url(), self.edit_data())

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            AuditLog.objects.filter(action=AuditLog.Action.LOG_EDITED).exists()
        )

    def test_edit_with_invalid_metadata_changes_nothing(self):
        for bad_metadata in ['{not json', '[1, 2]']:
            with self.subTest(bad_metadata):
                response = self.client.post(
                    self.edit_url(), self.edit_data(metadata=bad_metadata)
                )

                self.assertEqual(response.status_code, 200)
                self.log.refresh_from_db()
                self.assertEqual(self.log.metadata, {'community_id': 7})
                self.assertFalse(
                    AuditLog.objects.filter(
                        action=AuditLog.Action.LOG_EDITED
                    ).exists()
                )

    def test_edit_with_unknown_action_is_rejected(self):
        response = self.client.post(
            self.edit_url(), self.edit_data(action='NOT_AN_ACTION')
        )

        self.assertEqual(response.status_code, 200)
        self.log.refresh_from_db()
        self.assertEqual(self.log.action, AuditLog.Action.MEMBER_ADDED)

    def test_an_edit_log_can_itself_be_edited_and_is_logged(self):
        self.client.post(self.edit_url(), self.edit_data(
            action=AuditLog.Action.MEMBER_BANNED
        ))
        edit_log = AuditLog.objects.get(action=AuditLog.Action.LOG_EDITED)

        self.client.post(
            reverse('logs:edit_log', args=[edit_log.id]),
            {
                'actor': self.admin.id,
                'action': AuditLog.Action.LOG_EDITED,
                'content_type': edit_log.content_type_id,
                'object_id': edit_log.object_id,
                'metadata': json.dumps({'note': 'corrigido'}),
            },
        )

        self.assertEqual(
            AuditLog.objects.filter(action=AuditLog.Action.LOG_EDITED).count(), 2
        )

    # ===== EXCLUIR =====
    def test_delete_removes_the_log_and_logs_the_deletion(self):
        log_id = self.log.id

        response = self.client.post(reverse('logs:delete_log', args=[log_id]))

        self.assertRedirects(response, reverse('logs:log_list'))
        self.assertFalse(AuditLog.objects.filter(id=log_id).exists())

        deletion = AuditLog.objects.get(action=AuditLog.Action.LOG_DELETED)
        self.assertEqual(deletion.actor, self.admin)
        self.assertEqual(
            deletion.content_type, ContentType.objects.get_for_model(AuditLog)
        )
        self.assertEqual(deletion.object_id, log_id)
        deleted = deletion.metadata['deleted_log']
        self.assertEqual(deleted['action'], AuditLog.Action.MEMBER_ADDED)
        self.assertEqual(deleted['actor'], self.owner.id)
        self.assertEqual(deleted['object_id'], self.reader.id)
        self.assertEqual(deleted['metadata'], {'community_id': 7})

    def test_delete_only_accepts_post(self):
        response = self.client.get(reverse('logs:delete_log', args=[self.log.id]))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(AuditLog.objects.filter(id=self.log.id).exists())
        self.assertFalse(
            AuditLog.objects.filter(action=AuditLog.Action.LOG_DELETED).exists()
        )

    def test_delete_missing_log_is_404(self):
        response = self.client.post(reverse('logs:delete_log', args=[999999]))

        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            AuditLog.objects.filter(action=AuditLog.Action.LOG_DELETED).exists()
        )


# ---------------------------------------------------------------------------
# As ações dos outros apps realmente geram logs
# ---------------------------------------------------------------------------
class ActionLoggingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = make_user('SiteAdmin', superuser=True)
        cls.owner = make_user('Owner')
        cls.moderator = make_user('Moderator')
        cls.member = make_user('Member')
        cls.outsider = make_user('Outsider')
        cls.applicant = make_user('Applicant')

        cls.community = CommunityService.create_community(
            Community.objects.create(name='NewCommunity', creator=cls.owner)
        )
        MembershipService.enter_community(cls.moderator, cls.community, role=Membership.Role.MODERATOR)
        MembershipService.enter_community(cls.member, cls.community)

        cls.private_community = CommunityService.create_community(
            Community.objects.create(
                name='PrivateCommunity',
                creator=cls.owner,
                access=Community.Access.PRIVATE,
            )
        )

    def setUp(self):
        self.client = Client()

    def membership_of(self, user, community=None):
        return Membership.objects.get(user=user, community=community or self.community)

    def logs(self, action, target):
        return AuditLog.objects.filter(
            action=action,
            content_type=ContentType.objects.get_for_model(target),
            object_id=target.pk,
        )

    def assert_logged(self, action, actor, target, **metadata):
        """Confere que existe exatamente um log da ação para o alvo, com o
        autor e (parte do) metadata esperados."""
        found = self.logs(action, target)
        self.assertEqual(found.count(), 1, f'{action} deveria ter sido registrado')
        log = found.get()
        self.assertEqual(log.actor, actor)
        for key, value in metadata.items():
            self.assertEqual(log.metadata.get(key), value)
        return log

    def assert_not_logged(self, action, target):
        self.assertFalse(self.logs(action, target).exists())

    # ===== COMUNIDADE =====
    def test_community_created_by_service(self):
        self.assert_logged(
            AuditLog.Action.COMMUNITY_CREATED, self.owner, self.community,
            community_id=self.community.id,
        )

    def test_community_created_by_view(self):
        self.client.force_login(self.member)

        self.client.post(reverse('communities:create_community'), {
            'name': 'ViaView',
            'description': 'Descrição',
            'access': Community.Access.PUBLIC,
        })

        community = Community.objects.get(name='ViaView')
        self.assert_logged(
            AuditLog.Action.COMMUNITY_CREATED, self.member, community,
            community_name='ViaView',
        )

    def test_community_update_is_logged_only_when_something_changed(self):
        self.client.force_login(self.owner)
        url = reverse('communities:edit_community', args=[self.community.id])
        data = {
            'name': self.community.name,
            'description': self.community.description,
            'access': self.community.access,
        }

        self.client.post(url, data)
        self.assert_not_logged(AuditLog.Action.COMMUNITY_UPDATED, self.community)

        self.client.post(url, {**data, 'name': 'Renamed'})
        log = self.assert_logged(
            AuditLog.Action.COMMUNITY_UPDATED, self.owner, self.community
        )
        self.assertIn('name', log.metadata['changed_fields'])

    def test_archive_and_unarchive_are_logged(self):
        self.client.force_login(self.owner)

        self.client.post(reverse('communities:archive_community', args=[self.community.id]))
        self.assert_logged(AuditLog.Action.COMMUNITY_ARCHIVED, self.owner, self.community)

        self.client.post(reverse('communities:unarchive_community', args=[self.community.id]))
        self.assert_logged(AuditLog.Action.COMMUNITY_UNARCHIVED, self.owner, self.community)

    def test_archive_by_unauthorized_user_is_not_logged(self):
        self.client.force_login(self.outsider)

        response = self.client.post(
            reverse('communities:archive_community', args=[self.community.id])
        )

        self.assertEqual(response.status_code, 403)
        self.assert_not_logged(AuditLog.Action.COMMUNITY_ARCHIVED, self.community)

    def test_community_deleted_is_logged(self):
        self.client.force_login(self.owner)
        community_id = self.community.id

        self.client.post(reverse('communities:delete_community', args=[community_id]))

        self.assertFalse(Community.objects.filter(id=community_id).exists())
        # a instância do teste continua com o ID, e o log também
        self.assert_logged(
            AuditLog.Action.COMMUNITY_DELETED, self.owner, self.community,
            community_name='NewCommunity',
        )

    def test_community_deleted_by_unauthorized_user_is_not_logged(self):
        self.client.force_login(self.outsider)

        response = self.client.post(
            reverse('communities:delete_community', args=[self.community.id])
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Community.objects.filter(id=self.community.id).exists())
        self.assert_not_logged(AuditLog.Action.COMMUNITY_DELETED, self.community)

    def test_purge_of_archived_communities_is_logged_without_actor(self):
        archived = CommunityService.create_community(
            Community.objects.create(
                name='Old', creator=self.owner, state=Community.State.ARCHIVED
            )
        )
        Community.objects.filter(id=archived.id).update(
            archived_at=timezone.now() - timedelta(days=61)
        )

        call_command('purge_archived_communities', stdout=StringIO())

        self.assertFalse(Community.objects.filter(id=archived.id).exists())
        self.assert_logged(
            AuditLog.Action.COMMUNITY_DELETED, None, archived,
            reason='archive_retention_expired',
        )

    # ===== MEMBROS =====
    def test_joining_a_public_community_is_logged(self):
        self.client.force_login(self.outsider)

        self.client.post(reverse('communities:join_community', args=[self.community.id]))

        self.assert_logged(
            AuditLog.Action.MEMBER_ADDED, self.outsider, self.outsider,
            community_id=self.community.id,
        )

    def test_request_to_join_a_private_community_is_not_a_member_added(self):
        self.client.force_login(self.applicant)

        self.client.post(
            reverse('communities:join_community', args=[self.private_community.id])
        )

        self.assertEqual(
            self.membership_of(self.applicant, self.private_community).status,
            Membership.Status.PENDING,
        )
        self.assert_not_logged(AuditLog.Action.MEMBER_ADDED, self.applicant)

    def test_accepting_a_request_is_logged(self):
        MembershipService.enter_community(
            self.applicant, self.private_community,
            role=Membership.Role.NONE, status=Membership.Status.PENDING,
        )
        membership = self.membership_of(self.applicant, self.private_community)
        self.client.force_login(self.owner)

        self.client.post(
            reverse('communities:manage_membership_request',
                    args=[self.private_community.id, membership.id]),
            {'decision': 'accept'},
        )

        self.assert_logged(
            AuditLog.Action.MEMBER_ADDED, self.owner, self.applicant,
            community_id=self.private_community.id, via='request',
        )

    def test_rejecting_a_request_is_logged(self):
        MembershipService.enter_community(
            self.applicant, self.private_community,
            role=Membership.Role.NONE, status=Membership.Status.PENDING,
        )
        membership = self.membership_of(self.applicant, self.private_community)
        self.client.force_login(self.owner)

        self.client.post(
            reverse('communities:manage_membership_request',
                    args=[self.private_community.id, membership.id]),
            {'decision': 'reject'},
        )

        self.assert_logged(
            AuditLog.Action.MEMBER_REQUEST_REJECTED, self.owner, self.applicant,
            community_id=self.private_community.id,
        )
        self.assert_not_logged(AuditLog.Action.MEMBER_ADDED, self.applicant)

    def test_leaving_a_community_is_logged(self):
        self.client.force_login(self.member)

        self.client.post(reverse('communities:leave_community', args=[self.community.id]))

        self.assertEqual(
            self.membership_of(self.member).status, Membership.Status.LEFT
        )
        self.assert_logged(
            AuditLog.Action.MEMBER_REMOVED, self.member, self.member,
            community_id=self.community.id, reason='left',
        )

    def test_last_member_leaving_logs_the_community_deletion(self):
        solo = CommunityService.create_community(
            Community.objects.create(name='Solo', creator=self.applicant)
        )
        self.client.force_login(self.applicant)

        self.client.post(reverse('communities:leave_community', args=[solo.id]))

        self.assertFalse(Community.objects.filter(id=solo.id).exists())
        self.assert_logged(
            AuditLog.Action.MEMBER_REMOVED, self.applicant, self.applicant,
            community_id=solo.id,
        )
        self.assert_logged(
            AuditLog.Action.COMMUNITY_DELETED, self.applicant, solo,
            reason='last_member_left',
        )

    def test_outsider_leaving_is_not_logged(self):
        self.client.force_login(self.outsider)

        response = self.client.post(
            reverse('communities:leave_community', args=[self.community.id])
        )

        self.assertEqual(response.status_code, 403)
        self.assert_not_logged(AuditLog.Action.MEMBER_REMOVED, self.outsider)

    def test_promotion_and_demotion_are_logged(self):
        self.client.force_login(self.owner)
        url = reverse(
            'communities:edit_member_role',
            args=[self.community.id, self.membership_of(self.member).id],
        )

        self.client.post(url, {'role': Membership.Role.MODERATOR})
        self.assert_logged(
            AuditLog.Action.MEMBER_PROMOTED, self.owner, self.member,
            community_id=self.community.id,
            old_role=Membership.Role.MEMBER, new_role=Membership.Role.MODERATOR,
        )

        self.client.post(url, {'role': Membership.Role.MEMBER})
        self.assert_logged(
            AuditLog.Action.MEMBER_DEMOTED, self.owner, self.member,
            community_id=self.community.id,
            old_role=Membership.Role.MODERATOR, new_role=Membership.Role.MEMBER,
        )

    def test_setting_the_same_role_is_not_logged(self):
        self.client.force_login(self.owner)

        self.client.post(
            reverse('communities:edit_member_role',
                    args=[self.community.id, self.membership_of(self.member).id]),
            {'role': Membership.Role.MEMBER},
        )

        self.assert_not_logged(AuditLog.Action.MEMBER_PROMOTED, self.member)
        self.assert_not_logged(AuditLog.Action.MEMBER_DEMOTED, self.member)

    def test_ban_and_unban_are_logged(self):
        self.client.force_login(self.owner)
        url = reverse(
            'communities:manage_member_ban',
            args=[self.community.id, self.membership_of(self.member).id],
        )

        self.client.post(url, {'decision': 'ban'})
        self.assertEqual(self.membership_of(self.member).status, Membership.Status.BANNED)
        self.assert_logged(
            AuditLog.Action.MEMBER_BANNED, self.owner, self.member,
            community_id=self.community.id,
        )

        self.client.post(url, {'decision': 'unban'})
        self.assert_logged(
            AuditLog.Action.MEMBER_UNBANNED, self.owner, self.member,
            community_id=self.community.id,
        )

    def test_ban_by_unauthorized_user_is_not_logged(self):
        self.client.force_login(self.member)

        response = self.client.post(
            reverse('communities:manage_member_ban',
                    args=[self.community.id, self.membership_of(self.moderator).id]),
            {'decision': 'ban'},
        )

        self.assertEqual(response.status_code, 403)
        self.assert_not_logged(AuditLog.Action.MEMBER_BANNED, self.moderator)

    # ===== FÓRUM =====
    def new_message(self, author):
        return Message.objects.create(
            forum=self.community.forum, author=author, content='Mensagem'
        )

    def test_message_deleted_by_moderator_is_logged(self):
        message = self.new_message(self.member)
        self.client.force_login(self.moderator)

        self.client.post(reverse('forums:delete_message', args=[message.id]))

        self.assertFalse(Message.objects.filter(id=message.id).exists())
        # a instância do teste mantém o ID, e o log também
        log = self.assert_logged(
            AuditLog.Action.MESSAGE_DELETED, self.moderator, message,
            forum_id=self.community.forum.id,
            community_id=self.community.id,
            message_author_id=self.member.id,
        )
        # o conteúdo da mensagem não é copiado para o log
        self.assertNotIn('Mensagem', json.dumps(log.metadata))

    def test_message_deleted_by_its_author_is_logged(self):
        message = self.new_message(self.member)
        self.client.force_login(self.member)

        self.client.post(reverse('forums:delete_message', args=[message.id]))

        self.assert_logged(
            AuditLog.Action.MESSAGE_DELETED, self.member, message
        )

    def test_message_deletion_by_unauthorized_user_is_not_logged(self):
        message = self.new_message(self.member)
        self.client.force_login(self.outsider)

        response = self.client.post(reverse('forums:delete_message', args=[message.id]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Message.objects.filter(id=message.id).exists())
        self.assert_not_logged(AuditLog.Action.MESSAGE_DELETED, message)
