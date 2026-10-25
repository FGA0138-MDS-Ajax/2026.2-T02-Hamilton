from django.conf import settings;
from django.core.validators import URLValidator;
from django.db import models;
from django.utils import timezone;

# CONSTANTES
COMMUNITY_NAME_LENGTH = 100;
COMMUNITY_DESC_LENGTH = 5000;
COMMUNITY_ICON_LENGTH = 500;

# Create your models here.

class Community(models.Model):
    class Access(models.TextChoices):
        PUBLIC = "PUBLIC", "Public";
        PRIVATE = "PRIVATE", "Private";

    class State(models.TextChoices):
        ACTIVE = "ACTIVE", "Active";
        ARCHIVED = "ARCHIVED", "Archived";

    name = models.CharField(
        max_length=COMMUNITY_NAME_LENGTH,
        blank=False,
    )
    # Endereço (URL http/https) da imagem da comunidade. Opcional: vazio = sem imagem.
    icon = models.CharField(
        max_length=COMMUNITY_ICON_LENGTH,
        blank=True,
        validators=[URLValidator(schemes=['http', 'https'])],
    )
    description = models.CharField(
        max_length=COMMUNITY_DESC_LENGTH,
        blank=True,
    )
    # Pública: qualquer um entra. Privada: o ingresso depende de aprovação.
    access = models.CharField(
        max_length=10,
        choices=Access.choices,
        default=Access.PUBLIC,
    )
    # Usuário que criou a comunidade.
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_communities",
    )
    state = models.CharField(
        max_length=10,
        choices=State.choices,
        default=State.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name;


class Membership(models.Model):
    class Role(models.TextChoices):
        NONE = "NONE", "None";
        MODERATOR = "MODERATOR", "Moderator";
        MEMBER = "MEMBER", "Member";

    class Status(models.TextChoices):
        NONE = "NONE", "None";
        PENDING = "PENDING", "Pending";
        ACTIVE = "ACTIVE", "Active";
        LEFT = "LEFT", "Left";
        BANNED = "BANNED", "Banned";

    # Integrante da comunidade (gera a coluna user_id).
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    # Comunidade da qual o usuário faz parte (gera a coluna community_id).
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    # Cargo do integrante nesta comunidade.
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.NONE,
    )
    # Situação da conexão entre o usuário e a comunidade.
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.NONE,
    )
    # Permite ordenar os membros para encontrar o mais antigo.
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            # Um usuário tem no máximo uma conexão por comunidade
            # (ao sair e voltar, a mesma linha é reaproveitada).
            models.UniqueConstraint(
                fields=["user", "community"],
                name="unique_user_community_membership",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.community} ({self.role}, {self.status})";