from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="profile"
    )
    # Ofensiva: dias consecutivos com pelo menos uma leitura registrada.
    # Positivo para impedir ofensivas negativas no banco (a view e os
    # métodos abaixo continuam sendo quem garante a regra de negócio).
    streak = models.PositiveIntegerField(
        default=0
    )
    # Último dia (data da leitura) que já foi contabilizado na ofensiva.
    last_read_date = models.DateField(
        null=True,
        blank=True
    )

    def reset_streak_if_broken(self, today=None) -> bool:
        """Zera a ofensiva se o usuário faltou pelo menos um dia inteiro.

        A ofensiva continua viva se a última leitura foi hoje ou ontem.
        Retorna True se a ofensiva foi zerada (campos alterados em memória;
        quem chama decide quando salvar).
        """
        today = today or timezone.localdate()
        if self.last_read_date is None or self.streak == 0:
            return False
        if self.last_read_date < today - timedelta(days=1):
            self.streak = 0
            return True
        return False

    def register_reading_day(self, reading_date, today=None) -> bool:
        """Contabiliza a data de uma leitura na ofensiva.

        - primeira leitura: streak = 1;
        - mesmo dia (ou data anterior à última contabilizada): não altera;
        - dia seguinte ao último contabilizado: streak + 1;
        - faltou algum dia: a ofensiva reseta e recomeça em 1.

        Levanta ValueError se a data estiver no futuro. Retorna True se a
        ofensiva mudou (quem chama decide quando salvar).
        """
        today = today or timezone.localdate()
        if reading_date > today:
            raise ValueError("A data da leitura não pode estar no futuro.")

        # A quebra é decidida pela distância entre a última leitura contabilizada
        # e a data DESTA leitura (não pela data de hoje); por isso não se chama
        # reset_streak_if_broken aqui: leituras retroativas em sequência
        # (ex.: dias -2, -1 e 0) seriam tratadas como ofensiva quebrada.
        if self.last_read_date is not None and reading_date <= self.last_read_date:
            return False  # já contado (ou leitura retroativa): não incrementa

        if (
            self.last_read_date is not None
            and reading_date == self.last_read_date + timedelta(days=1)
        ):
            self.streak += 1
        else:
            self.streak = 1
        self.last_read_date = reading_date
        return True

    def __str__(self):
        return f"Perfil de {self.user}"
