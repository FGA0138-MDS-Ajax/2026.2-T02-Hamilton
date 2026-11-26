import json

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models


class AuditLog(models.Model):
    """Registro de uma ação relevante feita no sistema (auditoria).

    O alvo da ação ("paciente") é guardado como classe (content_type) mais o
    ID do objeto (object_id), e não como chave estrangeira para o objeto. Assim
    um mesmo model serve para alvos de classes diferentes (User, Community,
    Message...) e o log continua existindo depois que o objeto é apagado.
    """

    class Action(models.TextChoices):
        # comunidades
        COMMUNITY_CREATED = "COMMUNITY_CREATED", "Community created"
        COMMUNITY_UPDATED = "COMMUNITY_UPDATED", "Community updated"
        COMMUNITY_ARCHIVED = "COMMUNITY_ARCHIVED", "Community archived"
        COMMUNITY_UNARCHIVED = "COMMUNITY_UNARCHIVED", "Community unarchived"
        COMMUNITY_DELETED = "COMMUNITY_DELETED", "Community deleted"
        # membros (o alvo é o usuário; a comunidade vai no metadata)
        MEMBER_ADDED = "MEMBER_ADDED", "Member added"
        MEMBER_REMOVED = "MEMBER_REMOVED", "Member removed"
        MEMBER_REQUEST_REJECTED = "MEMBER_REQUEST_REJECTED", "Member request rejected"
        MEMBER_PROMOTED = "MEMBER_PROMOTED", "Member promoted"
        MEMBER_DEMOTED = "MEMBER_DEMOTED", "Member demoted"
        MEMBER_BANNED = "MEMBER_BANNED", "Member banned"
        MEMBER_UNBANNED = "MEMBER_UNBANNED", "Member unbanned"
        # fóruns
        MESSAGE_DELETED = "MESSAGE_DELETED", "Message deleted"
        # os próprios logs (ações dos administradores sobre eles)
        LOG_EDITED = "LOG_EDITED", "Log edited"
        LOG_DELETED = "LOG_DELETED", "Log deleted"

    CATEGORY_CHOICES = [
        ("", "Todas as categorias"),
        ("communities", "Comunidades"),
        ("members", "Membros"),
        ("forums", "Fóruns"),
        ("logs", "Logs"),
    ]

    CATEGORY_ACTION_MAP = {
        "communities": [
            Action.COMMUNITY_CREATED,
            Action.COMMUNITY_UPDATED,
            Action.COMMUNITY_ARCHIVED,
            Action.COMMUNITY_UNARCHIVED,
            Action.COMMUNITY_DELETED,
        ],
        "members": [
            Action.MEMBER_ADDED,
            Action.MEMBER_REMOVED,
            Action.MEMBER_REQUEST_REJECTED,
            Action.MEMBER_PROMOTED,
            Action.MEMBER_DEMOTED,
            Action.MEMBER_BANNED,
            Action.MEMBER_UNBANNED,
        ],
        "forums": [
            Action.MESSAGE_DELETED,
        ],
        "logs": [
            Action.LOG_EDITED,
            Action.LOG_DELETED,
        ],
    }

    # Usuário que executou a ação. SET_NULL (e não CASCADE) para o histórico
    # sobreviver à exclusão do usuário. Nulo também quando quem agiu foi o
    # sistema (ex.: purge_archived_communities).
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(
        max_length=50,
        choices=Action.choices,
    )
    # Classe do alvo da ação (User, Community, Message...).
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        related_name="+",
    )
    # ID do alvo (inteiro, e não o objeto em si).
    object_id = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    # Informações complementares (ex.: id da comunidade, cargo anterior).
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["content_type", "object_id"],
                name="logs_target_idx",
            ),
        ]

    def get_target(self):
        """Retorna o objeto alvo, ou None se ele não existe mais."""
        model = self.content_type.model_class()
        if model is None:
            return None
        return model._default_manager.filter(pk=self.object_id).first()

    @property
    def category(self) -> str:
        """Categoria amigável da ação."""
        if self.action.startswith("COMMUNITY_"):
            return "Comunidades"
        if self.action.startswith("MEMBER_"):
            return "Membros"
        if self.action.startswith("MESSAGE_"):
            return "Fóruns"
        if self.action.startswith("LOG_"):
            return "Logs"
        return "Geral"

    @property
    def metadata_pretty(self) -> str:
        """Metadata formatado como JSON legível (usado nos templates)."""
        return json.dumps(self.metadata, indent=2, ensure_ascii=False)

    def to_snapshot(self) -> dict:
        """Cópia simples (só tipos JSON) dos campos do log.

        Usada para registrar o que mudou quando um administrador edita um
        log, e o que existia quando ele o exclui.
        """
        return {
            "actor": self.actor_id,
            "action": self.action,
            "content_type": f"{self.content_type.app_label}.{self.content_type.model}",
            "object_id": self.object_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __str__(self):
        return f"{self.action} em {self.content_type.model} #{self.object_id}"
