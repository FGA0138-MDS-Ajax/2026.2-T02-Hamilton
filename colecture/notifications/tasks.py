from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from goals.models import ReadingSession
from .models import Notification

@shared_task
def notify_without_reading():
    today = timezone.localdate()

    User = get_user_model()
    users = User.objects.all()

    for user in users:
        has_reading = ReadingSession.objects.filter(
            user=user,
            date=today,
        ).exists()

        already_notified = Notification.objects.filter(
            target_user=user,
            content='Você já leu hoje? Não se esqueça de registrar sua leitura diária!',
            created_at__date=today
        ).exists()
        

        if not has_reading and not already_notified:
                 
            Notification.objects.create(
                target_user=user,
                content='Você já leu hoje? Não se esqueça de registrar sua leitura diária!'
            )
        

        