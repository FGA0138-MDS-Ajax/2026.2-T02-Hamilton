from django.db import models
from django.contrib.auth import get_user_model;

# CONSTANTES
COMMUNITY_NAME_LENGTH = 100;
COMMUNITY_DESC_LENGTH = 5000;

# Create your models here.

class Community_STUB(models.Model):
    class State(models.TextChoices):
        ACTIVE = "ACTIVE", "Active";
        ARCHIVED = "ARCHIVED", "Archived";

    name = models.CharField(
        max_length=COMMUNITY_NAME_LENGTH,
        blank=False,
    )
    description = models.CharField(
        max_length=COMMUNITY_DESC_LENGTH,
        blank=True
    )
    state = models.CharField(
        choices=State.choices,
        default=State.ACTIVE
    )
    creator = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name="created_communities"
    )
