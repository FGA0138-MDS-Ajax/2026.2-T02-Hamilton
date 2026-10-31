from django.db import models
from django.db.models import Q;

# Create your models here.
class Forum(models.Model):
    class State(models.TextChoices):
        ACTIVE = "ACTIVE", "Active";
        LOCKED = "LOCKED", "Locked";
    community = models.ForeignKey(
        "communities.Community",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="forums"
    );

    goal = models.ForeignKey(
        "goals.Goal",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    );

    state = models.CharField(
        choices=State.choices,
        default=State.ACTIVE
    );

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(community__isnull=False, goal__isnull=True) |
                    Q(community__isnull=True, goal__isnull=False)
                ),
                name="exclusive_parent_constraint"
            ),
        ];



