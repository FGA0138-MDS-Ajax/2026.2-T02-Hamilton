from django.urls import reverse;
from django.utils.timezone import localtime;
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

    @staticmethod
    def build_page_data(forum, user, forum_messages)->dict:
        """Dados que o forum.js (communities/forum.html) lê para montar a página
        de qualquer fórum: o geral da comunidade ou o de uma meta."""
        community = ForumService.get_forum_parent_community(forum);
        goal = forum.goal;

        if goal:
            kind = "meta";
            description = goal.description;
            back_url = reverse("goals:view_goal", args=[goal.id]);
            back_label = "Voltar para a comunidade";
        else:
            kind = "geral";
            description = community.description;
            back_url = reverse("communities:view_community", args=[community.id]);
            back_label = "Voltar para a comunidade";

        return {
            "id": forum.id,
            "title": forum.name,
            "description": description,
            "kind": kind,
            "meta_name": goal.name if goal else "",
            # o menu de moderação do front (fixar/trancar/excluir) ainda não
            # tem backend; trancar e editar continuam em forums:edit_forum.
            "is_moderator": False,
            "locked": forum.state != forum.State.ACTIVE,
            "pinned_id": None,
            "current_user": user.username,
            "created_by": community.creator.username,
            "community_url": back_url,
            "back_label": back_label,
            "messages": [
                {
                    "id": message.id,
                    "author": message.author.username,
                    "text": message.content,
                    "time": localtime(message.created_at).strftime("%d/%m %H:%M"),
                    "mine": message.author_id == user.id,
                    "reply_to": None,
                }
                for message in forum_messages
            ],
        };