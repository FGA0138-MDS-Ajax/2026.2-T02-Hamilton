from .models import Membership;

class MembershipService:
    @staticmethod
    def user_in_community(user, community)->bool:
        return (community.creator == user) or (
            Membership.objects.filter(
                user=user,
                community=community,
                status=Membership.Status.ACTIVE
            ).exists()
        )

    @staticmethod
    def user_can_manage(user, community)->bool:
        """Administrador, criador ou moderador ativo da comunidade."""
        return (
            user.is_superuser
            or community.creator_id == user.id
            or Membership.objects.filter(
                user=user,
                community=community,
                role=Membership.Role.MODERATOR,
                status=Membership.Status.ACTIVE
            ).exists()
        )
