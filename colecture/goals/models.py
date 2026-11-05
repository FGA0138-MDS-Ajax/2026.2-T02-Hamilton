from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from books.models import Book

GOAL_NAME_MAX_LENGTH = 100


class Goal(models.Model):
    class GoalType(models.TextChoices):
        PAGE_COUNT = "PAGE_COUNT", "Pages"
        HOUR_COUNT = "HOUR_COUNT", "Hours"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        CONCLUDED = "CONCLUDED", "Concluded"
        PAUSED = "PAUSED", "Paused"

    name = models.CharField(max_length=GOAL_NAME_MAX_LENGTH, blank=False)

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
    # Quantidade do goal_type a ser atingida (ex.: 10000 páginas).
    target = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    # Livro relacionado à meta. Opcional: se o livro for excluído, a meta continua.
    book = models.ForeignKey(
        "books.Book",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="goals",
    )
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

    @property
    def forum(self):
        # Forum.goal é uma FK sem related_name, então o reverso é forum_set.
        return self.forum_set.first()

    @property
    def time_remaining(self):
        if self.deadline is None:
            return None
        return max(self.deadline - timezone.now(), timedelta(0))

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
    
class ReadingSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reading_sessions"
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="reading_sessions"
    )

    page_start = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    page_end = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    minute_count = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    date = models.DateField(default=timezone.localdate)

    def clean(self):
        super().clean()

        errors = {}

        #verifica se a pagina inicial é menor que a final
        if (
            self.page_start is not None
            and self.page_end is not None
            and self.page_start > self.page_end
        ):
            errors["page_start"] = (
                "A página inicial não pode ser maior que a página final."
            )

        #verifica se o intervalo não ultrapassa o total de páginas do livro
        if self.book_id and self.page_end is not None:
            if self.book.pages is None:
                errors["book"] = (
                    "O livro precisa ter a quantidade de páginas informada."
                )
            elif self.page_end > self.book.pages:
                errors["page_end"] = (
                    "A página final não pode ultrapassar o total de páginas do livro."
                )

        #impede sobreposição de páginas para o mesmo usuário e livro
        if (
            self.user_id
            and self.book_id
            and self.page_start is not None
            and self.page_end is not None
            and self.page_start <= self.page_end
        ):
            overlapping_sessions = ReadingSession.objects.filter(
                user_id=self.user_id,
                book_id=self.book_id,
                page_start__lte=self.page_end,
                page_end__gte=self.page_start,
            )

            #exclui o próprio registro quando estiver sendo editado
            if self.pk:
                overlapping_sessions = overlapping_sessions.exclude(
                    pk=self.pk
                )

            if overlapping_sessions.exists():
                errors["page_start"] = (
                    "Esse intervalo de páginas já possui um registro de leitura."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.user} - {self.book} ({self.date})"
