from django.apps import AppConfig


class GoalsConfig(AppConfig):
    name = 'goals'

    def ready(self):
        # registra os signals (desativar GoalParticipation ao sair da comunidade)
        from . import signals  # noqa: F401
