from communities.services import MembershipService;

class ForumService:
    @staticmethod
    def get_forum_parent_community(forum):
        return forum.community or forum.goal.community;

    @staticmethod
    def user_can_edit(user, forum)->bool:
        parent_community = ForumService.get_forum_parent_community(forum);
        return MembershipService.user_can_manage(user, parent_community);