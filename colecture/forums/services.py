from communities.models import Community;
from communities.services import MembershipService;
from goals.services import GoalService;

class ForumService:
    @staticmethod
    def get_forum_parent_community(forum):
        # fórum geral: a comunidade é o pai direto.
        # fórum de meta: a comunidade é a dona da meta
        # (Goal.owner_community; só metas coletivas têm fórum).
        return forum.community or forum.goal.owner_community;

    @staticmethod
    def user_can_view(user, forum)->bool:
        """
        Quem pode ler e escrever no fórum.

        - Administrador, criador e moderadores da comunidade podem entrar
          em qualquer fórum dela (precisam dele para moderar).
        - Os demais só entram se a comunidade estiver ativa (mesma regra
          da página da comunidade) e:
            * fórum geral: forem membros da comunidade;
            * fórum de meta: participarem da meta.
        """
        parent_community = ForumService.get_forum_parent_community(forum);

        if MembershipService.user_can_manage(user, parent_community):
            return True;

        if parent_community.state != Community.State.ACTIVE:
            return False;

        if forum.community_id:
            return MembershipService.user_in_community(user, parent_community);

        return GoalService.user_participates(user, forum.goal);

    @staticmethod
    def user_can_edit(user, forum)->bool:
        parent_community = ForumService.get_forum_parent_community(forum);
        return MembershipService.user_can_manage(user, parent_community);

    @staticmethod
    def user_can_delete_message(user, message)->bool:
        """O autor, ou quem gerencia a comunidade do fórum (inclui admin)."""
        parent_community = ForumService.get_forum_parent_community(message.forum);
        return (
            message.author_id == user.id
            or MembershipService.user_can_manage(user, parent_community)
        );