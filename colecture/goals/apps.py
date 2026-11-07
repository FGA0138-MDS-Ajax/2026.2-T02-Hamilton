from django.apps import AppConfig


class GoalsConfig(AppConfig):
    name = 'goals'

    def ready(self):
        # registra os signals (sincronizar GoalParticipation com a Membership:
        # entrar nas metas ao entrar na comunidade, sair delas ao sair)
        from . import signals  # noqa: F401