from django.contrib import admin

from .models import Goal, GoalParticipation


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ("name", "owner_community", "owner_profile", "goal_type", "target", "status")
    list_filter = ("status", "goal_type")


@admin.register(GoalParticipation)
class GoalParticipationAdmin(admin.ModelAdmin):
    list_display = ("goal", "user", "state", "joined_at")
    list_filter = ("state",)
