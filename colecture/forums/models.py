from django.db import models
from django.db.models import Q;
from django.conf import settings;

FORUM_NAME_MAX_LENGTH = 100;
MESSAGE_MAX_LENGTH = 5000;

# Create your models here.
class Forum(models.Model):
    class State(models.TextChoices):
        ACTIVE = "ACTIVE", "Active";
        LOCKED = "LOCKED", "Locked";

    name = models.CharField(
        max_length=FORUM_NAME_MAX_LENGTH,
        blank=False,
    );
    
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
        max_length=20,
        choices=State.choices,
        default=State.ACTIVE
    );

    def __str__(self):
        return self.name;

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

class Message(models.Model):
    forum = models.ForeignKey(
        Forum,
        on_delete=models.CASCADE,
        related_name="messages"
    );

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=False,
        blank=False,
    );

    created_at = models.DateTimeField(
        auto_now_add=True
    );

    content = models.TextField(
        max_length=MESSAGE_MAX_LENGTH
    );

    def __str__(self):
        return f"""
Message in Forum \"{self.forum}\" created at {self.created_at} by {self.author}:
{self.content}
"""