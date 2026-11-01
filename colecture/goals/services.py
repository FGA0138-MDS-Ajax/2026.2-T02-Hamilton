from .models import GoalParticipation;

class GoalService:
    @staticmethod
    def user_participates(user, goal):
        return GoalParticipation.objects.filter(
            user=user,
            goal=goal,
            state=GoalParticipation.State.ACTIVE
        ).exists();