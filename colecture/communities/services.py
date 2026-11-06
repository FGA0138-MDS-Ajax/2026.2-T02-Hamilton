from datetime import timedelta;

from django.utils import timezone;
from django.utils.crypto import get_random_string;
from django.utils import timezone;

from .models import Membership, Invitation, INVITATION_EXPIRATION, INVITATION_CODE_LENGTH;
from forums.models import Forum, FORUM_NAME_MAX_LENGTH;

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

    @staticmethod
    def delete_invitation(community, invitation_code):
        invitation = Invitation.objects.filter(
            community=community,
            invitation_code=invitation_code
        ).first();

        if invitation:
            invitation.delete();
    
    @staticmethod
    def generate_invitation(community):
        invitation = Invitation();

        invitation.invitation_code = get_random_string(length=INVITATION_CODE_LENGTH);
        invitation.community = community;
        invitation.expires_at = timezone.now() + timedelta(minutes=INVITATION_EXPIRATION);
        invitation.save();

        return invitation;

class CommunityService:
    @staticmethod
    def create_community(community, creator=None, icon=None):
        community.creator = creator or community.creator;
        community.icon = icon or "";
        community.save();

        # forum principal de comunidade. O nome é cortado para caber
        # no limite do campo (o nome da comunidade já pode ter 100
        # caracteres) e get_or_create evita um segundo fórum geral
        # se a função for chamada de novo para a mesma comunidade.
        Forum.objects.get_or_create(
            community=community,
            defaults={'name':(community.name+" Forum")[:FORUM_NAME_MAX_LENGTH]},
        );

        return community;
