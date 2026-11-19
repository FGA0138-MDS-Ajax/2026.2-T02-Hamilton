from .models import Notification


def create_notification(target_user, content):
    return Notification.objects.create(
        target_user=target_user,
        content=content
    )