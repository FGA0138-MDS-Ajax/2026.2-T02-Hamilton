from django.contrib.auth import get_user_model;
from django.db import models

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="profile"
    );
    streak = models.IntegerField(
        default=0
    );
