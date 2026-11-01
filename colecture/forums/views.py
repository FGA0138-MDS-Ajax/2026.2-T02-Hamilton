from django.shortcuts import render, get_object_or_404, redirect;
from django.views import View;
from django.contrib.auth.mixins import LoginRequiredMixin;
from .models import Forum, Message;
from .forms import MessageForm;
from communities.services import MembershipService;
from goals.services import GoalService;

# Create your views here.
class ViewForum(View, LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return self.handle_no_permission();

        view_permission_checks = [
            self.is_forum_visible,
        ];
    
        self.user = request.user;
        self.forum = get_object_or_404(Forum, id=kwargs['forum_id']);
        self.forum_parent_community = self.forum.community;
        self.forum_parent_goal = self.forum.goal;

        for check in view_permission_checks:
            if check()==False:
                return self.handle_no_permission();

        return super().dispatch(request, *args, **kwargs);

    def is_forum_visible(self):
        if self.forum_parent_community:
            # o fórum pertence à uma comunidade.
            # verificar se o usuário é membro da comunidade
            return MembershipService.user_in_community(
                self.user,
                self.forum_parent_community
            );
        elif self.forum_parent_goal:
            # o fórum pertence à uma meta.
            # verificar se o usuário participa da meta
            return GoalService.user_participates(
                self.user,
                self.forum_parent_goal
            );
        return False;

    def post(self, request, *args, **kwargs):
        form = MessageForm(request.POST);

        if form.is_valid():
            message_instance = form.save(commit=False);

            message_instance.forum = self.forum;
            message_instance.author = self.user;

            message_instance.save();

            # temporário, quando o front puder receber o json
            # para atualizar sem dar reload eu atualizo aqui.
            return redirect("forums:view_forum", forum_id = self.forum.id);
            

    def get(self, request, *args, **kwargs):
        return render(
            request, 
            "forums/forum_view.html", 
            {
                'forum':self.forum,
                'messages':self.forum.messages,
                'form':MessageForm()
            }
        );
