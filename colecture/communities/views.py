from django.shortcuts import get_object_or_404, render, redirect;
from django.contrib.auth import get_user_model;
from django.http import HttpResponseForbidden;
from django.contrib.auth.decorators import login_required
from .forms import CommunityForm
from .models import Community, Membership;

# Create your views here.
def view_community(request, community_id):
    community = Community.objects.filter(id=community_id).first();

    if community is None:
        return render(request, "communities/community_view.html", {'community':None});

    # pegando valores importantes
    user = request.user;

    # calculando lógica
    user_is_eligible = user.is_superuser or (community.creator == user);
    community_is_archived = community.state == Community.State.ARCHIVED;

    if community_is_archived and not user_is_eligible:
        return HttpResponseForbidden();

    if request.method == "GET":
        community_info = {
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