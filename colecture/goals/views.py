from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from communities.models import Community
from communities.services import MembershipService

from accounts.models import Profile;
from .forms import GoalForm, IndividualGoalForm;
from .models import Goal;
from .services import GoalService

from books.models import BookStatus



def _redirect_after_goal(goal):
    if goal.owner_community_id:
        return redirect("communities:view_community", community_id=goal.owner_community_id)
    return redirect("accounts:profile")


def _render_individual_form(request, form, is_edit, goal=None):
    return render(
        request, "goals/individual_goal_form.html",
        {"form": form, "is_edit": is_edit, "goal": goal},
    )


def _create_goal(request, instance):
    individual = instance.owner_profile_id is not None
    form_class = IndividualGoalForm if individual else GoalForm
    if request.method == "POST":
        form = form_class(request.POST, instance=instance)
        if form.is_valid():
            goal = GoalService.create_goal(form.save(commit=False), request.user)
            messages.success(request, f'Meta "{goal.name}" criada!')
            return _redirect_after_goal(goal)
        messages.error(request, "Não foi possível criar a meta. Verifique os campos.")
    else:
        form = form_class(instance=instance)
    if individual:
        return _render_individual_form(request, form, is_edit=False)
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
    if request.method == "GET" and GoalService.current_individual_goals(profile).exists():
        messages.error(request, "Você já tem uma meta ativa. Conclua ou exclua a atual para criar outra.")
        return redirect("accounts:profile")
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

    form_class = GoalForm if goal.is_collective else IndividualGoalForm
    if request.method == "POST":
        form = form_class(request.POST, instance=goal)
        if form.is_valid():
            GoalService.update_goal(form.save(commit=False))
            messages.success(request, "Meta atualizada!")
            return _redirect_after_goal(goal)
        messages.error(request, "Não foi possível salvar. Verifique os campos.")
    else:
        form = form_class(instance=goal)
    if not goal.is_collective:
        return _render_individual_form(request, form, is_edit=True, goal=goal)
    return render(
        request, "goals/goal_form.html",
        {"form": form, "is_edit": True, "goal": goal},
    )


@login_required
@require_POST
def delete_goal(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id)
    if goal.is_collective or not GoalService.user_can_manage(request.user, goal):
        return HttpResponseForbidden()
    name = goal.name
    goal.delete()
    messages.success(request, f'Meta "{name}" excluída.')
    return redirect("accounts:profile")


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