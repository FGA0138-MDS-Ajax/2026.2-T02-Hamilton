from django.db import models
from django.conf import settings;

# Create your models here.
class Goal(models.Model):
    pass;

class GoalParticipation(models.Model):
    class State(models.TextChoices):
        ACTIVE = "ACTIVE", "Active",
        INACTIVE = "INACTIVE", "Inactive"

    goal = models.ForeignKey(
        Goal,
        on_delete=models.CASCADE,
        related_name="participations"
    );

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="goal_participations"
    );

    state = models.CharField(
        max_length=20,
        choices=State.choices,
        default=State.ACTIVE
    );