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
        