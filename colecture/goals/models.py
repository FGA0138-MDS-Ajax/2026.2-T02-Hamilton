from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from books.models import Book

GOAL_NAME_MAX_LENGTH = 100
GOAL_DESC_MAX_LENGTH = 500


class Goal(models.Model):
    class GoalType(models.TextChoices):
        PAGE_COUNT = "PAGE_COUNT", "Páginas"
        HOUR_COUNT = "HOUR_COUNT", "Horas"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Ativa"
        CONCLUDED = "CONCLUDED", "Concluída"
        PAUSED = "PAUSED", "Pausada"

    class Period(models.TextChoices):
        DAILY = "DAILY", "Todo dia"
        WEEKDAYS = "WEEKDAYS", "Dias específicos"
        WEEKLY = "WEEKLY", "Por semana"
        MONTHLY = "MONTHLY", "Por mês"
        TOTAL = "TOTAL", "No total"

    name = models.CharField(max_length=GOAL_NAME_MAX_LENGTH, blank=False)
    # Texto livre opcional explicando o objetivo da meta.
    description = models.CharField(max_length=GOAL_DESC_MAX_LENGTH, blank=True)

    # Dono: comunidade OU perfil, nunca ambos (ver CheckConstraint abaixo).
    owner_community = models.ForeignKey(
        "communities.Community",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="goals",
    )
    owner_profile = models.ForeignKey(
        "accounts.Profile",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="goals",
    )

    goal_type = models.CharField(max_length=20, choices=GoalType.choices)
    # Prazo opcional.
    deadline = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    # Quantidade do goal_type a ser atingida: páginas (PAGE_COUNT) ou
    # MINUTOS (HOUR_COUNT; o form recebe HH:MM e converte).
    target = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    # Livro relacionado à meta. Opcional: se o livro for excluído, a meta continua.
    book = models.ForeignKey(
        "books.Book",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="goals",
    )
    period = models.CharField(
        max_length=10,
        choices=Period.choices,
        default=Period.TOTAL,
    )
    weekdays = models.CharField(max_length=13, blank=True)
    emoji = models.CharField(max_length=8, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # exatamente um dono: comunidade XOR perfil
            models.CheckConstraint(
                condition=(
                    Q(owner_community__isnull=False, owner_profile__isnull=True)
                    | Q(owner_community__isnull=True, owner_profile__isnull=False)
                ),
                name="goal_exclusive_owner_constraint",
            ),
        ]

    def clean(self):
        super().clean()
        # O ModelForm ignora constraints que usam campos fora do form
        # (os donos não são editáveis), então a regra é repetida aqui.
        if (self.owner_community_id is None) == (self.owner_profile_id is None):
            raise ValidationError(
                "A meta deve pertencer a uma comunidade ou a um perfil, não a ambos."
            )

    @property
    def is_collective(self) -> bool:
        return self.owner_community_id is not None

    # O fórum da meta é o reverso do OneToOneField Forum.goal
    # (related_name="forum"), e não uma propriedade deste model.
    # Metas individuais não têm fórum: use GoalService.get_forum(goal),
    # que devolve None em vez de levantar Forum.DoesNotExist.

    @property
    def time_remaining(self):
        if self.deadline is None:
            return None
        return max(self.deadline - timezone.now(), timedelta(0))

    @property
    def target_display(self) -> str:
        """Alvo legível: '300 páginas' ou '22h10' / '10h'."""
        if self.goal_type == self.GoalType.HOUR_COUNT:
            hours, minutes = divmod(self.target, 60)
            return f"{hours}h{minutes:02d}" if minutes else f"{hours}h"
        return f"{self.target} páginas"

    @property
    def weekday_list(self) -> list[int]:
        return [int(d) for d in self.weekdays.split(",") if d.strip().isdigit()]

    def __str__(self):
        return self.name


class GoalParticipation(models.Model):
    class State(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    goal = models.ForeignKey(
        Goal,
        on_delete=models.CASCADE,
        related_name="participations",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="goal_participations",
    )
    # Data de inserção do usuário na meta (atualizada na reinscrição).
    joined_at = models.DateTimeField(default=timezone.now)
    state = models.CharField(
        max_length=20,
        choices=State.choices,
        default=State.ACTIVE,
    )

    class Meta:
        constraints = [
            # Um usuário tem no máximo uma participação por meta
            # (ao sair e voltar, a mesma linha é reaproveitada).
            models.UniqueConstraint(
                fields=["goal", "user"],
                name="unique_goal_user_participation",
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.goal} ({self.state})"
