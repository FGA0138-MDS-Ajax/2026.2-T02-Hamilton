from django.contrib import admin
from .models import Profile
from rewards.services import check_streak


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        check_streak(obj.user)