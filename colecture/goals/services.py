import math
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.contrib.auth import get_user_model;

from communities.models import Community, Membership
from communities.services import MembershipService
from forums.models import Forum
from books.models import ReadingSession;

from .models import Goal, GoalParticipation

GOAL_UNIT_LABELS = {
    Goal.GoalType.PAGE_COUNT: "páginas",
    Goal.GoalType.HOUR_COUNT: "horas",
}

WEEKDAY_LABELS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]

PERIOD_PROGRESS_LABELS = {
    Goal.Period.DAILY: "hoje",
    Goal.Period.WEEKDAYS: "hoje",
    Goal.Period.WEEKLY: "nesta semana",
    Goal.Period.MONTHLY: "neste mês",
    Goal.Period.TOTAL: "no total",
}

PERIOD_SCHEDULE_LABELS = {
    Goal.Period.DAILY: "por dia",
    Goal.Period.WEEKLY: "por semana",
    Goal.Period.MONTHLY: "por mês",
    Goal.Period.TOTAL: "no total",
}


def _format_amount(goal, amount) -> str:
    if goal.goal_type == Goal.GoalType.HOUR_COUNT:
        hours, minutes = divmod(amount, 60)
        if not hours:
            return f"{minutes}min"
        return f"{hours}h{minutes:02d}" if minutes else f"{hours}h"
    return str(amount)


class GoalService:
    # ---------- permissões ----------
    @staticmethod
    def user_participates(user, goal):
        return GoalParticipation.objects.filter(
            user=user,
            goal=goal,
            state=GoalParticipation.State.ACTIVE
        ).exists()

    @staticmethod
    def user_can_view(user, goal) -> bool:
        if user.is_superuser:
            return True
        if goal.owner_profile_id:
            return goal.owner_profile.user_id == user.id
        return MembershipService.user_in_community(user, goal.owner_community)

    @staticmethod
    def user_can_manage(user, goal) -> bool:
        if user.is_superuser:
            return True
        if goal.owner_profile_id:
            return goal.owner_profile.user_id == user.id
        return MembershipService.user_can_manage(user, goal.owner_community)

    # ---------- criação / edição ----------
    @staticmethod
    @transaction.atomic
    def create_goal(goal: Goal, creator) -> Goal:
        """goal: instância já validada (form.save(commit=False))."""
        # isinstance (e não type ==): request.user é um SimpleLazyObject
        creator_is_a_user = isinstance(creator, get_user_model());
        if goal.is_collective:
            # meta de comunidade sempre usa o livro atual da comunidade
            # (o form não tem campo livro); só vale na criação, para que
            # trocar o livro da comunidade depois não altere metas antigas
            goal.book = goal.owner_community.book
        goal.save()
        if goal.is_collective:
            # só metas coletivas têm fórum
            Forum.objects.create(name=goal.name[:100], goal=goal)
            # meta de comunidade: todos os membros (e o criador da
            # comunidade) entram automaticamente, inclusive quem criou a meta
            GoalService.join_all_members(goal)
        elif creator_is_a_user:
            # meta individual: o dono entra na própria meta
            GoalService.join(creator, goal)
        return goal

    @staticmethod
    def get_forum(goal):
        """Fórum da meta, ou None (metas individuais não têm fórum)."""
        # goal.forum (reverso do OneToOne) levanta Forum.DoesNotExist quando
        # não há fórum; por isso a consulta direta.
        return Forum.objects.filter(goal=goal).first()

    @staticmethod
    @transaction.atomic
    def update_goal(goal: Goal) -> Goal:
        goal.save()
        forum = GoalService.get_forum(goal)
        if forum and forum.name != goal.name[:100]:
            forum.name = goal.name[:100]
            forum.save(update_fields=["name"])
        return goal

    # ---------- participação ----------
    @staticmethod
    @transaction.atomic
    def join(user, goal):
        """
        Inscreve (ou reinscreve) o usuário na meta.
        Retorna (participation, changed). Levanta ValidationError se não puder.
        """
        if goal.status != Goal.Status.ACTIVE:
            raise ValidationError("Só é possível entrar em metas ativas.")

        if goal.is_collective:
            community = goal.owner_community
            if community.state != Community.State.ACTIVE:
                raise ValidationError("Esta comunidade não está disponível.")
            # user_in_community já considera o criador (que não tem Membership)
            if not MembershipService.user_in_community(user, community):
                raise ValidationError(
                    "Você precisa ser membro da comunidade para entrar nesta meta."
                )
        elif goal.owner_profile.user_id != user.id:
            raise ValidationError("Metas individuais só podem ser seguidas pelo dono.")

        participation, created = GoalParticipation.objects.get_or_create(
            goal=goal, user=user
        )
        if created:
            return participation, True
        if participation.state == GoalParticipation.State.ACTIVE:
            return participation, False  # já inscrito: idempotente

        # reinscrição: reativa a mesma linha
        participation.state = GoalParticipation.State.ACTIVE
        participation.joined_at = timezone.now()
        participation.save(update_fields=["state", "joined_at"])
        return participation, True

    @staticmethod
    @transaction.atomic
    def join_all_members(goal) -> int:
        """
        Inscreve na meta coletiva todos os membros ativos da comunidade e o
        seu criador (que não possui Membership). Usado na criação da meta.

        Só cria as participações que faltam: não reativa quem saiu da meta.
        Metas que não estão ativas, individuais ou de comunidades
        arquivadas não recebem ninguém. Retorna quantas foram criadas.
        """
        if not goal.is_collective or goal.status != Goal.Status.ACTIVE:
            return 0
        community = goal.owner_community
        if community.state != Community.State.ACTIVE:
            return 0

        user_ids = set(
            Membership.objects.filter(
                community=community,
                status=Membership.Status.ACTIVE,
            ).values_list("user_id", flat=True)
        )
        user_ids.add(community.creator_id)

        already_in = set(
            GoalParticipation.objects.filter(
                goal=goal, user_id__in=user_ids
            ).values_list("user_id", flat=True)
        )
        GoalParticipation.objects.bulk_create([
            GoalParticipation(goal=goal, user_id=user_id)
            for user_id in user_ids - already_in
        ])
        return len(user_ids - already_in)

    @staticmethod
    def join_active_goals(user, community) -> int:
        """
        Inscreve o usuário em todas as metas ativas da comunidade (chamado
        quando ele passa a ser membro ativo). Também reativa participações
        antigas, desativadas quando ele saiu da comunidade.
        Retorna quantas participações foram criadas ou reativadas.
        """
        if community.state != Community.State.ACTIVE:
            return 0
        changed_count = 0
        for goal in community.goals.filter(status=Goal.Status.ACTIVE):
            try:
                _, changed = GoalService.join(user, goal)
            except ValidationError:
                continue  # meta/comunidade indisponível: não bloqueia a entrada
            changed_count += int(changed)
        return changed_count

    @staticmethod
    def leave(user, goal) -> int:
        """Desativa a participação. Retorna quantas foram desativadas (0 ou 1)."""
        return GoalParticipation.objects.filter(
            user=user,
            goal=goal,
            state=GoalParticipation.State.ACTIVE,
        ).update(state=GoalParticipation.State.INACTIVE)

    @staticmethod
    def deactivate_for_community_exit(user, community) -> int:
        """Desativa as participações do usuário nas metas da comunidade."""
        return GoalParticipation.objects.filter(
            user=user,
            goal__owner_community=community,
            state=GoalParticipation.State.ACTIVE,
        ).update(state=GoalParticipation.State.INACTIVE)

    # ---------- conclusão ----------
    @staticmethod
    def conclude(goal) -> bool:
        if goal.status == Goal.Status.CONCLUDED:
            return False
        goal.status = Goal.Status.CONCLUDED
        goal.save(update_fields=["status"])
        return True

    # ---------- cards da comunidade ----------
    @staticmethod
    def days_remaining(goal):
        remaining = goal.time_remaining
        if remaining is None:
            return None
        return math.ceil(remaining.total_seconds() / 86400)

    @staticmethod
    def get_completion(goal) -> dict:
        # concluiu quem contribuiu com pelo menos o alvo da meta
        participations = list(
            goal.participations.filter(state=GoalParticipation.State.ACTIVE)
        )
        done = sum(
            1 for p in participations
            if GoalService.get_user_contribution(p) >= goal.target
        )
        return {"done": done, "total": len(participations)}

    @staticmethod
    def build_community_cards(community) -> dict:
        goals = list(
            community.goals
            .select_related("book")
            .order_by("-created_at")
        )
        forums = {}
        for forum in Forum.objects.filter(goal__in=goals).order_by("id"):
            forums.setdefault(forum.goal_id, forum)

        cards = {"active": [], "closed": []}
        for goal in goals:
            closed = goal.status == Goal.Status.CONCLUDED
            cards["closed" if closed else "active"].append({
                "goal": goal,
                "closed": closed,
                "unit": GOAL_UNIT_LABELS.get(goal.goal_type, ""),
                "progress": GoalService.get_progress(goal),
                "completion": GoalService.get_completion(goal),
                "days_remaining": GoalService.days_remaining(goal),
                "forum": forums.get(goal.id),
            })
        return cards

    # ---------- contribuição / progresso ----------
    @staticmethod
    def get_user_contribution(participation) -> int:
        """Total lido pelo participante, desde que entrou na meta, no livro
        da meta: páginas (PAGE_COUNT) ou minutos (HOUR_COUNT)."""
        goal = participation.goal

        if not goal.book and goal.is_collective:
            return 0

        # session.date é uma data local; joined_at é UTC, então converte
        # antes de pegar a data (senão a leitura do dia da entrada, feita à
        # noite, ficaria de fora)
        sessions = ReadingSession.objects.filter(
            user=participation.user,
            date__gte=timezone.localtime(participation.joined_at).date()
        )
        if goal.book:
            sessions = sessions.filter(book=goal.book)

        if goal.goal_type == Goal.GoalType.PAGE_COUNT:
            # sessões sem pages_read (livros sem total de páginas, registradas em
            # percentual) não contam para metas de páginas
            contribution = sessions.filter(
                pages_read__isnull=False
            ).aggregate(
                total=Coalesce(Sum("pages_read"), 0)
            )["total"]

        elif goal.goal_type == Goal.GoalType.HOUR_COUNT:
            contribution = sessions.aggregate(
                total=Sum("minute_count")
            )["total"]

        else:
            return 0

        return contribution or 0

    @staticmethod
    def get_progress(goal) -> dict:
        total = sum(
            GoalService.get_user_contribution(p) for p in goal.participations.all()
        )
        percent = min(100, round(total / goal.target * 100)) if goal.target else 0
        return {"current": total, "target": goal.target, "percent": percent}

    @staticmethod
    def current_individual_goals(profile):
        return (
            Goal.objects.filter(owner_profile=profile)
            .exclude(status=Goal.Status.CONCLUDED)
        )

    @staticmethod
    def get_current_individual_goal(profile):
        return (
            GoalService.current_individual_goals(profile)
            .select_related("book")
            .order_by("-created_at")
            .first()
        )

    @staticmethod
    def period_range(goal, today=None):
        today = today or timezone.localdate()
        if goal.period in (Goal.Period.DAILY, Goal.Period.WEEKDAYS):
            return today, today
        if goal.period == Goal.Period.WEEKLY:
            return today - timedelta(days=today.weekday()), today
        if goal.period == Goal.Period.MONTHLY:
            return today.replace(day=1), today
        return None, today

    @staticmethod
    def describe_schedule(goal) -> str:
        amount = _format_amount(goal, goal.target)
        if goal.goal_type == Goal.GoalType.PAGE_COUNT:
            amount = f"{amount} páginas"
        if goal.period == Goal.Period.WEEKDAYS:
            days = ", ".join(WEEKDAY_LABELS[d] for d in goal.weekday_list if 0 <= d <= 6)
            return f"{amount} · {days}" if days else amount
        return f"{amount} {PERIOD_SCHEDULE_LABELS.get(goal.period, '')}".strip()

    @staticmethod
    def get_individual_progress(goal) -> dict:
        today = timezone.localdate()
        start, end = GoalService.period_range(goal, today)
        created = timezone.localtime(goal.created_at).date()
        start = max(start, created) if start else created

        sessions = ReadingSession.objects.filter(
            user_id=goal.owner_profile.user_id,
            date__gte=start,
            date__lte=end,
        )
        if goal.book_id:
            sessions = sessions.filter(book_id=goal.book_id)

        if goal.goal_type == Goal.GoalType.HOUR_COUNT:
            field = "minute_count"
        else:
            # metas de páginas ignoram sessões com pages_read nulo (registradas
            # em percentual); metas de horas continuam contando todas as sessões
            field = "pages_read"
            sessions = sessions.filter(pages_read__isnull=False)
        current = sessions.aggregate(total=Coalesce(Sum(field), 0))["total"] or 0
        target = goal.target
        remaining = max(target - current, 0)

        weekdays = goal.weekday_list
        rest_day = goal.period == Goal.Period.WEEKDAYS and today.weekday() not in weekdays
        next_day = None
        if rest_day and weekdays:
            next_day = WEEKDAY_LABELS[min(
                weekdays, key=lambda d: (d - today.weekday()) % 7
            )]

        return {
            "current": current,
            "target": target,
            "percent": min(100, round(current / target * 100)) if target else 0,
            "done": current >= target,
            "current_display": _format_amount(goal, current),
            "target_display": _format_amount(goal, target),
            "remaining_display": _format_amount(goal, remaining),
            "unit": "páginas" if goal.goal_type == Goal.GoalType.PAGE_COUNT else "",
            "period_label": PERIOD_PROGRESS_LABELS.get(goal.period, ""),
            "schedule": GoalService.describe_schedule(goal),
            "rest_day": rest_day,
            "next_day": next_day,
            "days_remaining": GoalService.days_remaining(goal),
            "start_date": start,
            "end_date": end,
        }
