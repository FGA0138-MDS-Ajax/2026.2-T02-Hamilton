from django.db import models
from django.utils import timezone
from django.conf import settings


# Create your models here.
class Notification(models.Model):
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    content = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)