from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


NAME_MAX_LENGTH = 100
DESCRIPTION_MAX_LENGTH = 150
CHOICE_MAX_LENGTH = 20

# Create your models here.
class CriteriaType(models.TextChoices):
    STREAK = 'STREAK', 'Ofensiva pessoal'
    BOOKS_READ = 'BOOKS_READ', 'Livros lidos'
    DAILY_PROGRESS = 'DAILY_PROGRESS', 'Progresso diário'
    HOURS_READ = 'HOURS_READ', 'Horas de leitura'
    INDIVIDUAL_GOAL = 'INDIVIDUAL_GOAL', 'Metas individuais'
    COMMUNITY = 'COMMUNITY', 'Comunidades'
    COMMUNITY_GOAL = 'COMMUNITY_GOAL', 'Metas de comunidade'
    SOCIAL = 'SOCIAL', 'Social, fórum e avaliações'
    SPECIAL = 'SPECIAL', 'Especiais'

class Insignia(models.Model):
    name = models.CharField(max_length=NAME_MAX_LENGTH)
    description = models.TextField(max_length=DESCRIPTION_MAX_LENGTH)
    icon = models.ImageField(upload_to='icon/') # Pasta de icones
    is_active = models.BooleanField(default=True)

    criteria_type = models.CharField(
         max_length =CHOICE_MAX_LENGTH,
         choices = CriteriaType.choices,       
    )

    criteria_value = models.IntegerField(
        validators=[MinValueValidator(1)]
    )

class Award(models.Model):
    insignia = models.ForeignKey(
        Insignia,
        on_delete=models.CASCADE,
        related_name='awards'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='awards'
    )
    awarded_at = models.DateTimeField(auto_now_add=True)


