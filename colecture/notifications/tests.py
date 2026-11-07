from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from books.models import Book
from goals.models import ReadingSession
from notifications.models import Notification
from notifications.tasks import notify_without_reading
from django.urls import reverse

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
            page_start=1,
            page_end=10,
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

