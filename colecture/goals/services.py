from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from communities.models import Community
from communities.services import MembershipService
from forums.models import Forum

from .models import Goal, GoalParticipation


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
        goal.save()
        if goal.is_collective:
            # só metas coletivas têm fórum
            Forum.objects.create(name=goal.name[:100], goal=goal)
        # o criador entra na própria meta (o admin pode não ser membro da comunidade)
        if (not goal.is_collective
                or MembershipService.user_in_community(creator, goal.owner_community)):
            GoalService.join(creator, goal)
        return goal

    @staticmethod
    @transaction.atomic
    def update_goal(goal: Goal) -> Goal:
        goal.save()
        forum = goal.forum
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

    # ---------- contribuição / progresso ----------
    @staticmethod
    def get_user_contribution(participation) -> int:
        # TODO (Sprint 5, R16): ReadingSession ainda não existe.
        # Quando existir (campos hipotéticos user, book, pages_read, minutes):
        #   sessions = ReadingSession.objects.filter(
        #       user=participation.user, book=participation.goal.book)
        #   PAGE_COUNT -> sessions.aggregate(Sum("pages_read"))["pages_read__sum"] or 0
        #   HOUR_COUNT -> (sessions.aggregate(Sum("minutes"))["minutes__sum"] or 0) // 60
        return 0

    @staticmethod
    def get_progress(goal) -> dict:
        total = sum(
            GoalService.get_user_contribution(p) for p in goal.participations.all()
        )
        percent = min(100, round(total / goal.target * 100)) if goal.target else 0
        return {"current": total, "target": goal.target, "percent": percent}
