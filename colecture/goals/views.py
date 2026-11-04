from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.models import Profile
from communities.models import Community
from communities.services import MembershipService

from .forms import GoalForm, ReadingSessionForm
from .models import Goal
from .services import GoalService


def _create_goal(request, instance):
    """Fluxo comum de criação; instance já vem com o dono definido."""
    if request.method == "POST":
        form = GoalForm(request.POST, instance=instance)
        if form.is_valid():
            goal = GoalService.create_goal(form.save(commit=False), request.user)
            messages.success(request, f'Meta "{goal.name}" criada!')
            return redirect("goals:view_goal", goal_id=goal.id)
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
def view_goal(request, goal_id):
    goal = get_object_or_404(
        Goal.objects.select_related("owner_community", "owner_profile__user", "book"),
        id=goal_id,
    )
    if not GoalService.user_can_view(request.user, goal):
        return HttpResponseForbidden()

    participates = GoalService.user_participates(request.user, goal)
    return render(request, "goals/goal_view.html", {
        "goal": goal,
        "progress": GoalService.get_progress(goal),
        "time_remaining": goal.time_remaining,
        # o fórum só é visível a quem participa da meta (ver ViewForum)
        "forum": goal.forum if participates else None,
        "participates": participates,
        "can_manage": GoalService.user_can_manage(request.user, goal),
        "can_join": not participates and goal.status == Goal.Status.ACTIVE,
    })


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
            return redirect("goals:view_goal", goal_id=goal.id)
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
    return redirect("goals:view_goal", goal_id=goal.id)


@login_required
@require_POST
def leave_goal(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id)
    if GoalService.leave(request.user, goal) == 0:
        messages.error(request, "Você não participa desta meta.")
    return redirect("goals:view_goal", goal_id=goal.id)

@login_required
def register_reading_session(request):
    if request.method == "POST":
        form = ReadingSessionForm(request.POST)

        if form.is_valid():
            reading_session = form.save(commit=False)
            reading_session.user = request.user
            reading_session.save()

            return redirect("goals:register_reading_session")

    else:
        form = ReadingSessionForm()

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
    return redirect("goals:view_goal", goal_id=goal.id)
