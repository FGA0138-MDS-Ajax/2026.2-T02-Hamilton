from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.models import Profile
from communities.models import Community
from communities.services import MembershipService

from .forms import GoalForm, ReadingSessionForm
from .models import Goal
from .services import GoalService


def _redirect_after_goal(goal):
    """A meta não tem página própria: depois das ações voltamos para a
    comunidade dona dela (ou para o início, no caso de meta individual)."""
    if goal.owner_community_id:
        return redirect("communities:view_community", community_id=goal.owner_community_id)
    return redirect("main:index")


def _create_goal(request, instance):
    """Fluxo comum de criação; instance já vem com o dono definido."""
    if request.method == "POST":
        form = GoalForm(request.POST, instance=instance)
        if form.is_valid():
            goal = GoalService.create_goal(form.save(commit=False), request.user)
            messages.success(request, f'Meta "{goal.name}" criada!')
            return _redirect_after_goal(goal)
        messages.error(request, "Não foi possível criar a meta. Verifique os campos.")
    else:
        form = GoalForm(instance=instance)
    return render(request, "goals/goal_form.html", {"form": form, "is_edit": False})


@login_required
def create_community_goal(request, community_id):
    community = get_object_or_404(Community, id=community_id)
    if not MembershipService.user_can_manage(request.user, community):
        return HttpResponseForbidden()
    if community.state != Community.State.ACTIVE:
        return HttpResponseForbidden("This community is not available.")
    return _create_goal(request, Goal(owner_community=community))


@login_required
def create_profile_goal(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return _create_goal(request, Goal(owner_profile=profile))


@login_required
def goal_forum(request, goal_id):
    """Atalho para o fórum da meta (equivale a communities:forum).

    A página do fórum é única (forums.views.ViewForum), que valida quem
    pode entrar; aqui só redirecionamos para ela.
    """
    forum = GoalService.get_forum(get_object_or_404(Goal, id=goal_id))
    if forum is None:
        # meta individual (ou meta antiga sem fórum): não há fórum para abrir
        raise Http404("Esta meta não possui fórum.")
    return redirect("forums:view_forum", forum_id=forum.id)


@login_required
def edit_goal(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id)
    if not GoalService.user_can_manage(request.user, goal):
        return HttpResponseForbidden()

    if request.method == "POST":
        form = GoalForm(request.POST, instance=goal)
        if form.is_valid():
            GoalService.update_goal(form.save(commit=False))
            messages.success(request, "Meta atualizada!")
            return _redirect_after_goal(goal)
        messages.error(request, "Não foi possível salvar. Verifique os campos.")
    else:
        form = GoalForm(instance=goal)
    return render(
        request, "goals/goal_form.html",
        {"form": form, "is_edit": True, "goal": goal},
    )


@login_required
@require_POST
def join_goal(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id)
    if not GoalService.user_can_view(request.user, goal):
        # quem não é da comunidade nem enxerga a meta
        return HttpResponseForbidden()
    try:
        GoalService.join(request.user, goal)
    except ValidationError as e:
        messages.error(request, " ".join(e.messages))
    return _redirect_after_goal(goal)


@login_required
@require_POST
def leave_goal(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id)
    if GoalService.leave(request.user, goal) == 0:
        messages.error(request, "Você não participa desta meta.")
    return _redirect_after_goal(goal)

@login_required
def register_reading_session(request):
    if request.method == "POST":
        form = ReadingSessionForm(request.POST, user=request.user)

        if form.is_valid():
            # sessão e ofensiva são salvas juntas: ou as duas, ou nenhuma
            with transaction.atomic():
                reading_session = form.save()
                profile, _ = Profile.objects.get_or_create(user=request.user)
                if profile.register_reading_day(reading_session.date):
                    profile.save(update_fields=["streak", "last_read_date"])
            return redirect("goals:register_reading_session")

    else:
        form = ReadingSessionForm(user=request.user)

    return render(
        request,
        "goals/register_reading_session.html",
        {"form": form}
    )

@login_required
@require_POST
def conclude_goal(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id)
    if not GoalService.user_can_manage(request.user, goal):
        return HttpResponseForbidden()

    if GoalService.conclude(goal):
        messages.success(request, f'Meta "{goal.name}" marcada como concluída.')
    else:
        messages.error(request, "Esta meta já está concluída.")

    nxt = request.POST.get("next", "")
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        return redirect(nxt)
    return _redirect_after_goal(goal)