from django.shortcuts import get_object_or_404, render, redirect;
from django.contrib.auth import get_user_model;
from django.contrib.auth.mixins import LoginRequiredMixin;
from django.http import HttpResponseForbidden, HttpResponseNotAllowed, JsonResponse, HttpResponse;
from django.views import View;
from django.contrib.auth.decorators import login_required
from .forms import CommunityForm
from .models import Community, Membership, Invitation;
from .services import CommunityService, MembershipService;
from django.utils import timezone;
from django.views.decorators.http import require_GET
from django.contrib import messages
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from forums.models import Forum
from goals.services import GoalService


def _redirect_back(request, community):
    """Volta para o `next` enviado pelo form (ex.: página de gerenciar),
    se for uma URL local segura; senão, para a página da comunidade."""
    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect("communities:view_community", community_id=community.id)


# Create your views here.

"""
JoinCommunityView é uma CBV (class based view) para 
manter a legibilidade dado que é uma view
multi-fatorada
"""
class JoinCommunityView(LoginRequiredMixin, View):
    # este método é chamado primeiro
    def dispatch(self, request, *args, **kwargs):
        # este dispatch consulta request.user antes de o LoginRequiredMixin
        # agir, então a checagem de login precisa vir primeiro.
        if not request.user.is_authenticated:
            return self.handle_no_permission();

        community_id = kwargs['community_id'];

        # mantém a comunidade e usuário para os
        # outros métodos usarem.
        self.invitation_code = kwargs.get('invitation_code');
        self.community = get_object_or_404(Community, id=community_id);
        self.user = request.user;
        self.membership = Membership.objects.filter(
            community=self.community,
            user=self.user
        ).first();
        self.invitation = self.invitation_code and Invitation.objects.filter(
            community=self.community,
            invitation_code=self.invitation_code,
        ).first();
    
        return super().dispatch(request, *args, **kwargs)

    # este método é chamado automaticamente 
    # se o método da requisição for POST
    def post(self, request, *args, **kwargs):

        # lista de métodos que irão validar a requisição
        validation = [
            self.community_not_available,
            self.user_is_member, # já é membro?
            self.user_is_banned, # está banido?
            self.request_is_pending, # já solicitou entrada?
            self.invitation_code_wrong,
        ];
        for check in validation:
            response = check();
            if response != None:
                return response;

        # se nenhum método retornar falha, o usuário
        # entra/solicita entrada na comunidade.
        return self.join_community();

    def invitation_code_wrong(self):
        # se for pública, ou o usuário não enviou
        # um código, não precisa verificar nada.
        if (self.community.access!=Community.Access.PRIVATE) or (
            not self.invitation_code
        ):
            return;

        return HttpResponseForbidden("Invitation code incorrect or expired") if (
            not self.invitation or self.invitation.is_expired) else None;

    def community_not_available(self):
        return (self.community.state!=Community.State.ACTIVE and
        HttpResponseForbidden("This community is not available.")) or None;

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
        entrance_allowed = not(community_is_private) or ( # a comunidade é pública OU
            community_is_private and self.invitation # é privada e o usuário enviou um código (validado antes)
        );

        MembershipService.enter_community(
            self.user,
            self.community,
            role = (
                # caso o usuário enviou o código correto (validado antes)
                # ele pode entrar direto.
                Membership.Role.MEMBER if entrance_allowed else
                Membership.Role.NONE
            ),
            status = (
                Membership.Status.ACTIVE if entrance_allowed else 
                Membership.Status.PENDING
            ),
            joined_at=timezone.now() if not community_is_private else None
        );

        if self.invitation_code:
            MembershipService.delete_invitation(
                self.community,
                self.invitation_code
            );

        return self.redirect_to_community();

class JoinByCodeView(JoinCommunityView):
    """
    Pedido de entrada feito pelo modal "Entrar em comunidade privada"
    da home. O usuário digita só o código; aqui descobrimos de qual
    comunidade ele é e seguimos o mesmo fluxo da JoinCommunityView
    (a solicitação fica PENDENTE até o moderador aceitar).
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission();

        code = request.POST.get('codigo', '').strip().upper();
        community = code and Community.objects.filter(
            code=code,
            access=Community.Access.PRIVATE,
        ).first();

        if not community:
            messages.error(request, "Código inválido. Confira com o moderador.");
            return redirect("communities:home_community");

        kwargs['community_id'] = community.id;
        return super().dispatch(request, *args, **kwargs);

    def join_community(self):
        # cria a solicitação (PENDENTE), mas mantém o usuário na home
        super().join_community();
        messages.success(self.request, "Solicitação enviada! Aguarde o moderador aceitar.");
        return redirect("communities:home_community");

    def request_is_pending(self):
        # já tinha pedido antes: só avisa, também sem sair da home
        if super().request_is_pending():
            messages.info(self.request, "Você já pediu para entrar. Aguarde o moderador.");
            return redirect("communities:home_community");


class LeaveCommunityView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission();

        self.community = get_object_or_404(Community, pk=kwargs["community_id"]);
        self.user = request.user;
        self.active_membership = Membership.objects.filter(
            user= self.user,
            community=self.community,
            status=Membership.Status.ACTIVE
        ).first();
        self.is_creator = self.community.creator == self.user;
        self.is_admin = self.user.is_superuser;
        self.user_count = Membership.objects.filter(
            community = self.community,
            status=Membership.Status.ACTIVE
        ).count() + 1; # o "+1" é o criador que não tem membership

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # só quem faz parte da comunidade pode sair dela. Sem esta checagem,
        # qualquer usuário logado apagaria uma comunidade que só tem o criador
        # (ver ec_last_member).
        if not (self.is_creator or self.active_membership):
            return HttpResponseForbidden();

        # casos de borda (ordem obrigatória)
        edge_cases = [
            self.ec_last_member,
            self.ec_is_creator,
        ];

        for ec in edge_cases:
            response = ec();
            if response!=None:
                return response;
        return self.leave_community();

    def ec_last_member(self):
        if self.user_count-1<=0: # último membro
            self.community.clean_up_and_delete();
            return self.return_to_profile();

    def ec_is_creator(self):
        if self.is_creator: # o criador saiu.
            # o criador não tem Membership, então o signal de goals não
            # dispara: as metas da comunidade são desativadas aqui
            GoalService.deactivate_for_community_exit(self.user, self.community);
            self.give_ownership_to_oldest_member(except_user=self.user);
            return self.return_to_profile();

    def give_ownership_to_oldest_member(self, except_user=None):
        # pegando todos os membros (menos o que vai sair) por ordem de ingresso.
        oldest_memberships = Membership.objects.filter(
            community=self.community,
            status=Membership.Status.ACTIVE,
        ).exclude(user=except_user).order_by("joined_at");

        if oldest_memberships.count()<=0:
            self.community.clean_up_and_delete();
            return;
        oldest_membership = oldest_memberships[0];
        oldest_member = oldest_membership.user;
        oldest_membership.delete(); # o criador não tem membership

        self.community.creator = oldest_member;
        self.community.save();

    def return_to_profile(self):
        return redirect("accounts:profile");

    def leave_community(self):
        if self.active_membership:
            self.active_membership.status = Membership.Status.LEFT;
            self.active_membership.save();
        return self.return_to_profile();

def _can_manage(user, community):
    """Administrador, criador ou moderador ativo da comunidade."""
    if user.is_superuser or community.creator_id == user.id:
        return True
    return Membership.objects.filter(
        community=community,
        user=user,
        role=Membership.Role.MODERATOR,
        status=Membership.Status.ACTIVE,
    ).exists()


@login_required
def view_community(request, community_id):
    community = Community.objects.select_related("creator", "book").filter(id=community_id).first()

    if community is None:
        return render(request, "communities/community_view.html", {'community': None}, status=404)

    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    # pegando valores importantes
    user = request.user
    membership = Membership.objects.filter(user=user, community=community).first()
    status = membership.status if membership else None

    is_banned = status == Membership.Status.BANNED
    is_pending = status == Membership.Status.PENDING
    is_active_member = status == Membership.Status.ACTIVE
    is_creator = community.creator_id == user.id
    can_manage = _can_manage(user, community)
    community_is_archived = community.state == Community.State.ARCHIVED

    if not can_manage:  # não é admin, dono nem moderador
        if is_banned:
            return HttpResponseForbidden("You've been banned from this community.")
        elif community_is_archived:
            return HttpResponseForbidden("This community is archived.")

    # o que o template pode mostrar para este usuário
    permissions = {
        "can_join": not (
            community_is_archived or user.is_superuser or is_creator
            or is_active_member or is_pending or is_banned
        ),
        "is_pending": is_pending,
        "can_edit": can_manage,
        "can_leave": is_creator or is_active_member,
        "can_archive": can_manage and not community_is_archived,
        # só quem gerencia cria metas, e apenas em comunidade ativa
        "can_create_goal": can_manage and not community_is_archived,
    }

    # metas e fórum geral só aparecem para quem participa da comunidade
    # (o criador não tem Membership, por isso is_creator) ou a gerencia
    is_member = is_creator or is_active_member
    can_see_content = is_member or can_manage
    goal_cards = GoalService.build_community_cards(community) if can_see_content else None
    general_forum = (
        Forum.objects.filter(community=community).first() if can_see_content else None
    )

    community_info = {
        'id': community.id,
        'name': community.name,
        'description': community.description,
        'creator_name': community.creator.username,
        'creator_id': community.creator.id,
        'is_private': community.access == Community.Access.PRIVATE,
        # só quem participa ou gerencia recebe o código para compartilhar
        'code': community.code if can_see_content else '',
    }

    return render(request, "communities/community_view.html", {
        'community': community_info,
        'book': community.book,
        'permissions': permissions,
        'is_member': is_member,
        'goal_cards': goal_cards,
        'general_forum': general_forum,
    })


@login_required
def create_community(request):
    if request.method == "POST":
        form = CommunityForm(request.POST)

        if form.is_valid():
            community = CommunityService.create_community(
                form.save(commit=False),
                request.user
            );
            
            messages.success(request, f'Comunidade "{community.name}" criada com sucesso!')
            return redirect("communities:home_community")

        messages.error(request, "Não foi possível criar a comunidade. Verifique os campos.")
    else:
        form = CommunityForm()

    return render(request, "communities/create_community.html", {"form": form})

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
        community.clean_up_and_delete();
        return redirect('communities:home_community')

    return HttpResponseForbidden()

@login_required
def moderator_view(request, community_id):
    community = get_object_or_404(Community, id=community_id);
    user = request.user;

    if not MembershipService.user_can_manage(user, community):
        return HttpResponseForbidden("Access restricted.");

    if request.method == "POST":
        return redirect(
            "communities:view_community", 
            community_id=community_id
        );

    members = Membership.objects.filter(
        community=community,
        status=Membership.Status.ACTIVE
    );
    pending_requests = Membership.objects.filter(
        community=community,
        status=Membership.Status.PENDING
    );

    return render(
        request, 
        'communities/moderator.html',
        context={
            'community':community,
            'members':members,
            'members_count':members.count()+1,
            'is_private':community.access==Community.Access.PRIVATE,
            'pending': pending_requests.exists() and pending_requests,

        }
    );

@login_required
def edit_community(request, community_id):
    # 1. Busca a comunidade no banco de dados
    community = get_object_or_404(Community, id=community_id)

    # 2. Verifica as permissões do usuário
    is_admin = request.user.is_superuser
    is_owner = community.creator == request.user

    is_moderator = Membership.objects.filter(
        community=community,
        user=request.user,
        role=Membership.Role.MODERATOR,
        status=Membership.Status.ACTIVE,
    ).exists()

    # 3. Impede a edição por usuários sem permissão
    if not (is_admin or is_owner or is_moderator):
        return HttpResponseForbidden()

    # 4. Processa o formulário enviado
    if request.method == "POST":
        form = CommunityForm(request.POST, instance=community)

        if form.is_valid():
            form.save()
            return redirect(
                "communities:view_community",
                community_id=community.id
            )

    # 5. Exibe o formulário preenchido com os dados atuais
    else:
        form = CommunityForm(instance=community)

    return render(
        request,
        "communities/edit_community.html",
        {"form": form, "community": community},
    )

@login_required
def edit_member_role(request, community_id, membership_id):
    community = get_object_or_404(Community, id=community_id)

    membership = get_object_or_404(
        Membership,
        id=membership_id,
        community=community,
    )

    # Verifica quem pode gerenciar os membros
    is_admin = request.user.is_superuser
    is_owner = community.creator == request.user

    is_moderator = Membership.objects.filter(
        community=community,
        user=request.user,
        role=Membership.Role.MODERATOR,
        status=Membership.Status.ACTIVE,
    ).exists()

    if not (is_admin or is_owner or is_moderator):
        return HttpResponseForbidden()

    # Somente aceita alterações enviadas por POST
    if request.method != "POST":
        return HttpResponseForbidden()

    # O membro precisa estar ativo
    if membership.status != Membership.Status.ACTIVE:
        return HttpResponseForbidden()

    # Recebe e valida o novo cargo
    new_role = request.POST.get("role")

    allowed_roles = [
        Membership.Role.MEMBER,
        Membership.Role.MODERATOR,
    ]

    if new_role not in allowed_roles:
        return HttpResponseForbidden()

    # Atualiza somente o cargo
    membership.role = new_role
    membership.save(update_fields=["role"])

    return _redirect_back(request, community)

@login_required
def manage_membership_request(request, community_id, membership_id):
    community = get_object_or_404(Community, id=community_id)
    
    membership = get_object_or_404(
        Membership,
        id=membership_id,
        community=community,
    )

    # Verifica quem pode gerenciar os membros
    is_admin = request.user.is_superuser
    is_owner = community.creator == request.user

    is_moderator = Membership.objects.filter(
        community=community,
        user=request.user,
        role=Membership.Role.MODERATOR,
        status=Membership.Status.ACTIVE,
    ).exists()    

    if not (is_admin or is_owner or is_moderator):
        return HttpResponseForbidden()

    if request.method != "POST":
        return HttpResponseForbidden()

    # Só permite gerenciar solicitações pendentes
    if membership.status != Membership.Status.PENDING:
        return HttpResponseForbidden()

    # Recebe a ação enviada pelo formulário
    decision = request.POST.get("decision")

    if decision == "accept":
        # aceitar = virar membro de fato: ativa, define o cargo e renova o
        # joined_at (usado para achar o membro mais antigo quando o criador sai)
        membership.status = Membership.Status.ACTIVE
        membership.role = Membership.Role.MEMBER
        membership.joined_at = timezone.now()

    elif decision == "reject":
        membership.status = Membership.Status.NONE
        membership.role = Membership.Role.NONE

    else:
        return HttpResponseForbidden()

    # Salva a alteração no banco
    membership.save(update_fields=["status", "role", "joined_at"])

    return _redirect_back(request, community)

@login_required
def manage_member_ban(request, community_id, membership_id):
    community = get_object_or_404(Community, id=community_id)

    membership = get_object_or_404(
        Membership,
        id=membership_id,
        community=community,
    )

    # Verifica as permissões
    is_admin = request.user.is_superuser
    is_owner = community.creator == request.user

    is_moderator = Membership.objects.filter(
        community=community,
        user=request.user,
        role=Membership.Role.MODERATOR,
        status=Membership.Status.ACTIVE,
    ).exists()

    if not (is_admin or is_owner or is_moderator):
        return HttpResponseForbidden()

    # Só aceita requisições POST
    if request.method != "POST":
        return HttpResponseForbidden()

    # Impede expulsar a si mesmo ou o dono da comunidade
    if membership.user == request.user:
        return HttpResponseForbidden()

    if membership.user == community.creator:
        return HttpResponseForbidden()

    # Recebe a decisão
    decision = request.POST.get("decision")

    if decision == "ban":
        # Só expulsa membros ativos
        if membership.status != Membership.Status.ACTIVE:
            return HttpResponseForbidden()

        membership.status = Membership.Status.BANNED

    elif decision == "unban":
        # Só revoga expulsões de membros banidos
        if membership.status != Membership.Status.BANNED:
            return HttpResponseForbidden()

        membership.status = Membership.Status.NONE

    else:
        return HttpResponseForbidden()

    # Salva somente o status
    membership.save(update_fields=["status"])

    return _redirect_back(request, community)



@login_required
def archive_community(request, community_id):
    community = get_object_or_404(Community, id=community_id)

    if not _can_manage(request.user, community):
        return HttpResponseForbidden()

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    # o save() do model preenche archived_at (contagem dos 60 dias)
    community.state = Community.State.ARCHIVED
    community.save()

    messages.success(request, f'Comunidade "{community.name}" arquivada.')
    return redirect("communities:home_community")


@login_required
def unarchive_community(request, community_id):
    community = get_object_or_404(Community, id=community_id)

    if not _can_manage(request.user, community):
        return HttpResponseForbidden()

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    if community.state != Community.State.ARCHIVED:
        return HttpResponseForbidden()

    # o save() do model limpa archived_at ao sair do estado arquivado
    community.state = Community.State.ACTIVE
    community.save()

    messages.success(request, f'Comunidade "{community.name}" desarquivada.')
    return redirect("communities:home_community")


SEARCH_LIMIT = 50

@require_GET
def search_communities(request):
    """Busca de comunidades públicas e ativas (usada por main/search.js)."""
    term = request.GET.get("q", "").strip()

    queryset = Community.objects.filter(
        access=Community.Access.PUBLIC,
        state=Community.State.ACTIVE,
    )
    for word in term.split():
        queryset = queryset.filter(
            Q(name__icontains=word) | Q(description__icontains=word)
        )

    queryset = queryset.annotate(
        active_members=Count(
            "memberships",
            filter=Q(memberships__status=Membership.Status.ACTIVE),
        )
    ).order_by("name")

    total = queryset.count()
    results = [
        {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "members_count": c.active_members + 1,  # +1 = criador (sem membership)
            "url": reverse("communities:view_community", kwargs={"community_id": c.id}),
        }
        for c in queryset[:SEARCH_LIMIT]
    ]

    return JsonResponse({"total": total, "results": results})


@login_required
def home_community(request):
    user = request.user

    # papéis do usuário nas comunidades em que ele é membro ativo
    roles = dict(
        Membership.objects.filter(user=user, status=Membership.Status.ACTIVE)
        .values_list("community_id", "role")
    )

    # comunidades em que o usuário modera (o criador também é moderador)
    moderated = Q(creator=user) | Q(
        id__in=[cid for cid, role in roles.items() if role == Membership.Role.MODERATOR]
    )

    # arquivadas só aparecem para quem modera; membros comuns não as veem
    communities = (
        Community.objects
        .filter(Q(creator=user) | Q(id__in=roles.keys()))
        .filter(~Q(state=Community.State.ARCHIVED) | moderated)
        .order_by("name")
    )

    # membros ativos por comunidade (sem depender do related_name)
    counts = dict(
        Membership.objects
        .filter(community__in=communities, status=Membership.Status.ACTIVE)
        .values_list("community")
        .annotate(n=Count("id"))
    )

    comunidades = []
    for c in communities:
        if c.creator_id == user.id:
            papel = "Criador"
        elif roles.get(c.id) == Membership.Role.MODERATOR:
            papel = "Moderador"
        else:
            papel = "Membro"
        comunidades.append({
            "pk": c.pk,
            "nome": c.name,
            "descricao": c.description,
            "membros_count": counts.get(c.id, 0) + 1,  # +1 = criador
            "privada": c.access == Community.Access.PRIVATE,
            "papel": papel,
            # o criador também é moderador
            "is_moderator": papel in ("Criador", "Moderador"),
            "arquivada": c.state == Community.State.ARCHIVED,
        })

    # arquivadas vão para o fim da lista (sort é estável: mantém a ordem por nome)
    comunidades.sort(key=lambda c: c["arquivada"])

    return render(request, "communities/home_community.html", {
        "comunidades": comunidades,
        "ativas_count": sum(1 for c in comunidades if not c["arquivada"]),
    })

@login_required
def forum_page(request, community_id):
    """Atalho para o fórum geral da comunidade.

    A página do fórum é única (forums.views.ViewForum, que renderiza
    communities/forum.html); aqui só redirecionamos para ela.
    """
    forum = get_object_or_404(Forum, community_id=community_id)
    return redirect("forums:view_forum", forum_id=forum.id)

def generate_invitation(request, community_id):
    community = get_object_or_404(Community, id=community_id);
    user = request.user;

    is_eligible = MembershipService.user_can_manage(user, community);

    if not is_eligible:
        return HttpResponseForbidden("Access Restricted");

    if request.method=="POST":
        return HttpResponse("Only GET method is allowed.");

    new_invitation = MembershipService.generate_invitation(
        community
    );

    return JsonResponse(
        data={
            'invitation_code':new_invitation.invitation_code
        }
    );
