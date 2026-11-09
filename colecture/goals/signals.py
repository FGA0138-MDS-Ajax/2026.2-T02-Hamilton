from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from communities.models import Membership

from .services import GoalService


@receiver(pre_save, sender=Membership)
def remember_previous_membership_status(sender, instance, **kwargs):
    """
    Guarda o status que a Membership tinha no banco antes do save, para o
    post_save saber se o usuário ACABOU de virar membro ativo (entrada,
    aprovação de solicitação ou volta à comunidade) ou se é só outra
    alteração em uma Membership que já era ativa (ex.: mudança de cargo).
    """
    if instance.pk is None:
        instance._previous_status = None
        return
    instance._previous_status = (
        Membership.objects.filter(pk=instance.pk)
        .values_list("status", flat=True)
        .first()
    )


@receiver(post_save, sender=Membership)
def sync_goal_participations_with_membership(sender, instance, **kwargs):
    """
    Mantém as participações em metas coerentes com a Membership.

    - Passou a ser ACTIVE (entrou direto, solicitação aprovada ou voltou):
      o usuário entra automaticamente nas metas ativas da comunidade.
      Só reage à MUDANÇA para ACTIVE, para que alterar o cargo de quem já
      era membro não reinscreva quem saiu de uma meta por conta própria.
    - Deixou de ser ACTIVE (LEFT = saída voluntária, BANNED = saída forçada,
      etc.): o usuário sai das metas da comunidade.

    O criador saindo é tratado em LeaveCommunityView.ec_is_creator, pois ele
    não possui Membership.
    """
    if kwargs.get("raw"):  # loaddata: não dispara regras de negócio
        return
    if instance.status == Membership.Status.ACTIVE:
        if getattr(instance, "_previous_status", None) != Membership.Status.ACTIVE:
            GoalService.join_active_goals(instance.user, instance.community)
    else:
        GoalService.deactivate_for_community_exit(instance.user, instance.community)