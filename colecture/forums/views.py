from django.shortcuts import render, get_object_or_404, redirect;
from django.http import HttpResponseForbidden, HttpResponse;
from django.views import View;
from django.contrib.auth.mixins import LoginRequiredMixin;
from .models import Forum, Message;
from .forms import MessageForm, ForumForm;
from communities.services import MembershipService;
from .services import ForumService;
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
        if self.forum.state!=Forum.State.ACTIVE:
            return HttpResponseForbidden("The forum is inactive!");
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

def delete_message(request, message_id):

    if request.method == "POST":
        message = get_object_or_404(Message, id=message_id);
        forum = message.forum;
        community = forum.community or forum.goal.owner_community;
        user = request.user;

        if not community:
            return HttpResponseForbidden("Could not find community that hosts this forum.");

        if forum.state!=Forum.State.ACTIVE:
            return HttpResponseForbidden("The forum is inactive!");

        # valida se o usuário pode deletar essa mensagem.
        is_eligible = user.is_superuser or (
            message.author == user) or (
                MembershipService.user_can_manage(user,community));

        if not is_eligible:
            return HttpResponseForbidden("You cannot delete this message.");

        message.delete();

        return redirect("forums:view_forum", forum_id=forum.id);

    return HttpResponse("Only POST method allowed.")

def edit_forum(request, forum_id):

    forum = get_object_or_404(Forum, id=forum_id);
    user = request.user;

    # valida se o usuário pode editar esse fórum.
    is_eligible = ForumService.user_can_edit(user, forum);

    if not is_eligible:
        return HttpResponseForbidden("You cannot edit this forum.");

    if request.method == "POST":
        form = ForumForm(data=request.POST, instance=forum);

        if form.is_valid():
            form.save();
            return redirect("forums:edit_forum", forum_id=forum_id);
    else:
        form = ForumForm(instance=forum);

    return render(request, "forums/edit_forum.html", {'form':form, 'forum':forum});