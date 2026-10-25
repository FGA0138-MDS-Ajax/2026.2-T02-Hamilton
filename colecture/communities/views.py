from django.shortcuts import render, get_object_or_404, render, redirect;
from django.contrib.auth import get_user_model;
from django.http import HttpResponseForbidden;
from .models import Community;

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