from django.db.models.signals import post_save
from django.dispatch import receiver

from communities.models import Membership

from .services import GoalService


@receiver(post_save, sender=Membership)
def deactivate_goal_participations_on_exit(sender, instance, **kwargs):
    """
    Quando a Membership deixa de ser ACTIVE (LEFT = saída voluntária,
    BANNED = saída forçada, etc.), o usuário sai das metas da comunidade.
    O criador saindo é tratado em LeaveCommunityView.ec_is_creator, pois ele
    não possui Membership.
    """
    if instance.status != Membership.Status.ACTIVE:
        GoalService.deactivate_for_community_exit(instance.user, instance.community)
