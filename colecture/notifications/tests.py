import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Profile
from books.models import Book, ReadingSession
from notifications.models import Notification
from notifications.tasks import notify_without_reading

# Create your tests here.

#Teste de notificação se o usuario não registrou nenhuma leitura diária
class Notification_Task_Tests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )

        self.book = Book.objects.create(
            isbn='9788532511010',
            title='Livro de Teste',
            author='Author de teste'
        )

    # teste usuario sem leitura registrada recebe notificação
    def test_notifications_withou_reading(self):
        notify_without_reading()

        notification = Notification.objects.filter(
            target_user=self.user
        )

        self.assertTrue(notification.exists())

        
    # teste usuario com leitura registrada nõa recebe notificação
    def test_not_notify_with_reading(self):
        ReadingSession.objects.create(
            user=self.user,
            book=self.book,
            pages_read=10,
            minute_count=30,
            date=timezone.localdate()
            
        )

        notify_without_reading()

        self.assertFalse(
            Notification.objects.filter(target_user=self.user).exists()
        )

    # Teste usuario não recebe notificações duplicadas
    def test_not_duplicate_notifications(self):
        notify_without_reading()
        notify_without_reading()

        notifications = Notification.objects.filter(
            target_user=self.user
        )

        self.assertEqual(notifications.count(),1)


    # Teste usuraio consegue dispensar notificações 
    def test_user_can_dismiss_notifications(self):
        notification = Notification.objects.create(
            target_user=self.user,
            content='Notificação de Testes'
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                'notifications:dismiss_notification',
                args=[notification.id]
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Notification.objects.filter(id=notification.id).exists()
        )


class NotificationProfileAndHistoryTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='leitor_notif',
            password='testpassword',
        )
        self.other_user = User.objects.create_user(
            username='outro_leitor',
            password='testpassword',
        )
        self.profile_url = reverse('accounts:profile')
        self.history_url = reverse('notifications:history')
        self.list_url = reverse('notifications:notification_list')

    def _create_notification(self, user, content, minutes_ago=0):
        notification = Notification.objects.create(
            target_user=user,
            content=content,
        )
        if minutes_ago:
            Notification.objects.filter(pk=notification.pk).update(
                created_at=timezone.now() - timedelta(minutes=minutes_ago)
            )
            notification.refresh_from_db()
        return notification

    def test_bell_and_popup_appear_on_profile_with_history_link(self):
        self.client.force_login(self.user)
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-notifications-open')
        self.assertContains(response, 'data-notifications-modal')
        self.assertContains(response, f'href="{self.history_url}"')
        self.assertContains(response, 'Ver histórico')

    def test_empty_state_appears_when_no_notifications(self):
        self.client.force_login(self.user)

        profile_response = self.client.get(self.profile_url)
        self.assertEqual(profile_response.status_code, 200)
        self.assertContains(profile_response, 'data-notifications-empty')
        self.assertContains(profile_response, 'Você não tem notificações')

        history_response = self.client.get(self.history_url)
        self.assertEqual(history_response.status_code, 200)
        self.assertContains(history_response, 'data-notifications-history-empty')
        self.assertContains(history_response, 'Você não tem notificações')

    def test_notifications_ordered_newest_to_oldest_in_profile_list_and_history(self):
        self._create_notification(self.user, 'Notificação antiga', minutes_ago=120)
        self._create_notification(self.user, 'Notificação intermediária', minutes_ago=60)
        self._create_notification(self.user, 'Notificação recente', minutes_ago=5)
        self._create_notification(self.other_user, 'Notificação de outro usuário', minutes_ago=1)

        self.client.force_login(self.user)

        profile_response = self.client.get(self.profile_url)
        profile_html = profile_response.content.decode()
        self.assertNotIn('Notificação de outro usuário', profile_html)
        self.assertLess(
            profile_html.index('Notificação recente'),
            profile_html.index('Notificação intermediária'),
        )
        self.assertLess(
            profile_html.index('Notificação intermediária'),
            profile_html.index('Notificação antiga'),
        )

        list_response = self.client.get(self.list_url)
        self.assertEqual(list_response.status_code, 200)
        contents = [item['content'] for item in list_response.json()['notifications']]
        self.assertEqual(
            contents,
            ['Notificação recente', 'Notificação intermediária', 'Notificação antiga'],
        )

        history_response = self.client.get(self.history_url)
        history_html = history_response.content.decode()
        self.assertNotIn('Notificação de outro usuário', history_html)
        self.assertLess(
            history_html.index('Notificação recente'),
            history_html.index('Notificação intermediária'),
        )
        self.assertLess(
            history_html.index('Notificação intermediária'),
            history_html.index('Notificação antiga'),
        )

    def test_history_shows_old_notifications_beyond_popup_limit(self):
        for i in range(1, 8):
            self._create_notification(
                self.user,
                f'Aviso número {i}',
                minutes_ago=(8 - i) * 30,
            )

        self.client.force_login(self.user)

        profile_response = self.client.get(self.profile_url)
        self.assertEqual(profile_response.context['notifications_count'], 7)
        self.assertEqual(len(profile_response.context['notifications']), 5)
        self.assertContains(profile_response, 'Aviso número 7')
        self.assertNotContains(profile_response, 'Aviso número 1')

        history_response = self.client.get(self.history_url)
        self.assertEqual(history_response.status_code, 200)
        for i in range(1, 8):
            self.assertContains(history_response, f'Aviso número {i}')

    def test_history_page_has_sidebar_and_requires_login(self):
        anon_response = self.client.get(self.history_url)
        self.assertEqual(anon_response.status_code, 302)
        self.assertIn(reverse('accounts:login'), anon_response.url)

        self.client.force_login(self.user)
        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="rail"')
        self.assertContains(response, f'href="{self.profile_url}"')
        self.assertContains(response, 'nav-item active')

    def test_reading_session_creates_pages_and_streak_notifications(self):
        book = Book.objects.create(
            isbn='9788535902778',
            title='Dom Casmurro',
            author='Machado de Assis',
            pages=256,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('books:save_reading_session', args=[book.id]),
            data=json.dumps({'pages_read': 25, 'minute_count': 30}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)

        profile_response = self.client.get(self.profile_url)
        self.assertContains(profile_response, '25 páginas lidas em &quot;Dom Casmurro&quot;')
        self.assertContains(profile_response, 'Sua ofensiva foi iniciada: 1 dia seguido de leitura!')

        history_response = self.client.get(self.history_url)
        self.assertContains(history_response, '25 páginas lidas em &quot;Dom Casmurro&quot;')
        self.assertContains(history_response, 'Sua ofensiva foi iniciada: 1 dia seguido de leitura!')

    def test_editing_reading_session_creates_updated_pages_notification(self):
        book = Book.objects.create(
            isbn='9788535914849',
            title='Memórias Póstumas',
            author='Machado de Assis',
            pages=200,
        )
        self.client.force_login(self.user)

        create_response = self.client.post(
            reverse('books:save_reading_session', args=[book.id]),
            data=json.dumps({'pages_read': 10, 'minute_count': 20}),
            content_type='application/json',
        )
        session_id = create_response.json()['session']['id']

        edit_response = self.client.post(
            reverse('books:edit_reading_session', args=[book.id, session_id]),
            data=json.dumps({'pages_read': 40}),
            content_type='application/json',
        )
        self.assertEqual(edit_response.status_code, 200)

        profile_response = self.client.get(self.profile_url)
        self.assertContains(
            profile_response,
            'Leitura atualizada em &quot;Memórias Póstumas&quot;: 40 páginas lidas (40/200 páginas).',
        )

    def test_streak_reminder_and_broken_streak_notifications_on_profile(self):
        today = timezone.localdate()
        profile = Profile.objects.create(
            user=self.user,
            streak=4,
            last_read_date=today - timedelta(days=1),
        )
        self.client.force_login(self.user)

        first_response = self.client.get(self.profile_url)
        self.assertContains(
            first_response,
            'Não perca sua ofensiva de 4 dias! Registre uma leitura hoje para manter sua sequência.',
        )

        self.client.get(self.profile_url)
        reminder_count = Notification.objects.filter(
            target_user=self.user,
            content__icontains='Não perca sua ofensiva de 4 dias',
        ).count()
        self.assertEqual(reminder_count, 1)

        profile.last_read_date = today - timedelta(days=3)
        profile.save(update_fields=['last_read_date'])

        broken_response = self.client.get(self.profile_url)
        self.assertContains(
            broken_response,
            'Sua ofensiva foi zerada porque você ficou sem registrar leitura.',
        )

