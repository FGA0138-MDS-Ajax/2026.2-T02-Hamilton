from django.shortcuts import get_object_or_404, render, redirect;
from django.contrib.auth import get_user_model;
from django.contrib.auth.mixins import LoginRequiredMixin;
from django.http import HttpResponseForbidden;
from django.views import View;
from django.contrib.auth.decorators import login_required
from .forms import CommunityForm
from .models import Community, Membership;

# Create your views here.

"""
JoinCommunityView é uma CBV (class based view) para 
manter a legibilidade dado que é uma view
multi-fatorada
"""
class JoinCommunityView(View, LoginRequiredMixin):
    # este método é chamado primeiro
    def dispatch(self, request, *args, **kwargs):
        community_id = kwargs['community_id'];

        # mantém a comunidade e usuário para os
        # outros métodos usarem.
        self.community = get_object_or_404(Community, id=community_id);
        self.user = request.user;
        self.membership = Membership.objects.filter(
            community=self.community,
            user=self.user
        ).first();
    
        return super().dispatch(request, *args, **kwargs)

    # este método é chamado automaticamente 
    # se o método da requisição for POST
    def post(self, request, *args, **kwargs):

        # lista de métodos que irão validar a requisição
        validation = [
            self.user_is_member, # já é membro?
            self.user_is_banned, # está banido?
            self.request_is_pending, # já solicitou entrada?
        ];
        for check in validation:
            response = check();
            if response != None:
                return response;

        # se nenhum método retornar falha, o usuário
        # entra/solicita entrada na comunidade.
        return self.join_community();

    def user_is_member(self):
        """
        O criador da comunidade não possui membership dela
        para não termos mais de uma maneira de verificar
        a autoria (quem tem membership.role == Creator e
        Community.creator).
        """
        return (self.community.creator == self.user and
        self.redirect_to_community()) or (self.membership and
        self.membership.status == Membership.Status.ACTIVE and
        self.redirect_to_community()) or None;

    def user_is_banned(self):
        return (self.membership and
            self.membership.status == Membership.Status.BANNED and
                HttpResponseForbidden("You've been banned from this community.")) or None;

    def request_is_pending(self):
        return (self.community.access == Community.Access.PRIVATE and
            self.membership and
            self.membership.status == Membership.Status.PENDING and
            self.redirect_to_community()) or None;

    def redirect_to_community(self, community_id=None):
        return redirect(
            "communities:view_community",
            community_id=community_id or self.community.id
        );

    def join_community(self):
        community_is_private = self.community.access == Community.Access.PRIVATE;
        membership = self.membership or Membership();

        membership.user = self.user;
        membership.community =self.community;
        membership.role = (
            Membership.Role.NONE if community_is_private else
            Membership.Role.MEMBER
        );

        membership.status = (
            Membership.Status.PENDING if community_is_private else 
            Membership.Status.ACTIVE
        );

        membership.save();

        return self.redirect_to_community();

def view_community(request, community_id):
    community = Community.objects.filter(id=community_id).first();

    if community is None:
        return render(request, "communities/community_view.html", {'community':None});

    # pegando valores importantes
    user = request.user;
    membership = Membership.objects.filter(
        user=user,
        community=community
    ).first();
    # usuário está banido?
    is_banned = membership and membership.status == Membership.Status.BANNED;

    # calculando lógica
    user_is_eligible = user.is_superuser or (community.creator == user);
    community_is_archived = community.state == Community.State.ARCHIVED;

    if not user_is_eligible: # não é admin nem dono
        if is_banned:
            return HttpResponseForbidden("You've been banned from this community.");
        elif community_is_archived:
            return HttpResponseForbidden("This community is archived.");

    if request.method == "GET":
        community_info = {
            'id':community.id,
            'name':community.name,
            'description':community.description,
            'creator_name':community.creator.username,
            'creator_id':community.creator.id
        };

        return render(request, "communities/community_view.html", {'community':community_info});

@login_required
def create_community(request):
    if request.method == "POST":
        form = CommunityForm(request.POST)

        if form.is_valid():
            community = form.save(commit=False)
            community.creator = request.user
            community.icon = ""
            community.save()

            return redirect("communities:create_community")

    else:
        form = CommunityForm()

    return render(
        request,
        "communities/create_community.html",
        {"form": form},
    )

@login_required
def delete_community(request, community_id):
    community = get_object_or_404(Community, id=community_id)

    is_owner = community.creator == request.user
    is_admin = request.user.is_superuser
    is_moderator = Membership.objects.filter(
        community=community,
        user=request.user,
        role=Membership.Role.MODERATOR,
        status=Membership.Status.ACTIVE,
    ).exists()

    if not(is_admin or is_owner or is_moderator):
        return HttpResponseForbidden()

    if request.method == "POST":
        community.delete()
        return redirect('communities:create_community')

    return HttpResponseForbidden()
