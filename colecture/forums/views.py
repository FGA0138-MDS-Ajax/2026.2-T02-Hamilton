from django.shortcuts import render, get_object_or_404, redirect;
from django.http import HttpResponseForbidden, HttpResponse;
from django.views import View;
from django.contrib import messages;
from django.contrib.auth.decorators import login_required;
from django.contrib.auth.mixins import LoginRequiredMixin;
from .models import Forum, Message;
from .forms import MessageForm, ForumForm;
from .services import ForumService;

# Create your views here.
class ViewForum(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return self.handle_no_permission();

        view_permission_checks = [
            self.is_forum_visible,
        ];

        self.user = request.user;
        self.forum = get_object_or_404(Forum, id=kwargs['forum_id']);
        self.forum_parent_community = ForumService.get_forum_parent_community(self.forum);
        self.forum_parent_goal = self.forum.goal;

        for check in view_permission_checks:
            if check()==False:
                return self.handle_no_permission();

        return super().dispatch(request, *args, **kwargs);

    def is_forum_visible(self):
        # a regra (membro da comunidade no fórum geral, participante
        # no fórum da meta, moderação em ambos) fica no ForumService
        # para poder ser testada sem uma requisição HTTP.
        return ForumService.user_can_view(self.user, self.forum);

    def post(self, request, *args, **kwargs):
        form = MessageForm(request.POST);
        if self.forum.state!=Forum.State.ACTIVE:
            # fórum trancado: nada é salvo, e o usuário volta para a
            # página do fórum com um aviso (em vez de um 403 sem template).
            messages.error(request, "Este fórum está trancado. Não é possível enviar mensagens.");
            return redirect("forums:view_forum", forum_id = self.forum.id);
        if form.is_valid():
            message_instance = form.save(commit=False);

            message_instance.forum = self.forum;
            message_instance.author = self.user;

            message_instance.save();

            # temporário, quando o front puder receber o json
            # para atualizar sem dar reload eu atualizo aqui.
            return redirect("forums:view_forum", forum_id = self.forum.id);

        # mensagem inválida (ex.: vazia ou maior que o limite):
        # reexibe o fórum com os erros do formulário.
        return self.render_forum(request, form, status=400);

    def get(self, request, *args, **kwargs):
        return self.render_forum(request, MessageForm());

    def render_forum(self, request, form, status=200):
        return render(
            request,
            "forums/forum_view.html",
            {
                'forum':self.forum,
                # não usar a chave 'messages': ela é do
                # django.contrib.messages (context processor).
                'forum_messages':self.forum.messages.select_related(
                    'author'
                ).order_by('created_at', 'id'),
                'form':form,
                'parent_community':self.forum_parent_community,
                'parent_goal':self.forum_parent_goal,
                'can_moderate':ForumService.user_can_edit(self.user, self.forum),
            },
            status=status
        );

@login_required
def delete_message(request, message_id):

    if request.method == "POST":
        message = get_object_or_404(Message, id=message_id);
        forum = message.forum;
        user = request.user;

        # valida se o usuário pode deletar essa mensagem.
        # (a comunidade é encontrada tanto para o fórum geral
        # quanto para o fórum de uma meta)
        if not ForumService.user_can_delete_message(user, message):
            return HttpResponseForbidden("You cannot delete this message.");

        # fórum trancado: a mensagem fica e o usuário volta ao fórum com
        # um aviso. A checagem vem depois da permissão para não revelar
        # o estado do fórum a quem nem poderia apagar a mensagem.
        if forum.state!=Forum.State.ACTIVE:
            messages.error(request, "Este fórum está trancado. Não é possível apagar mensagens.");
            return redirect("forums:view_forum", forum_id=forum.id);

        message.delete();

        return redirect("forums:view_forum", forum_id=forum.id);

    return HttpResponse("Only POST method allowed.")

@login_required
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