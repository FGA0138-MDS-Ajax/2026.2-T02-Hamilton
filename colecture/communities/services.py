from django.utils import timezone;

from .models import Membership;
from forums.models import Forum;

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

    @staticmethod
    def enter_community(
            user, 
            community, 
            role=Membership.Role.MEMBER,
            status=Membership.Status.ACTIVE,
            joined_at=None
        ):
        membership = Membership.objects.filter(
            user=user,
            community=community
        ).first() or Membership();
        
        membership.role=role or (
            status==Membership.Status.ACTIVE and Membership.Role.MEMBER 
        ) or Membership.Role.NONE;
        membership.status=status;
        membership.user=user;
        membership.community=community;
        if joined_at:
            membership.joined_at = joined_at

        membership.save();

        return membership;

class CommunityService:
    @staticmethod
    def create_community(community, creator=None, icon=None):
        community.creator = creator or community.creator;
        community.icon = icon or "";
        community.save();

        # forum principal de comunidade
        main_forum = Forum.objects.create(
            name=community.name+" Forum",
            community=community,
        );

        return community;