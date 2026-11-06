from django.contrib import admin
from .models import Community, Membership, Invitation;

# Register your models here.
admin.site.register(Invitation);
admin.site.register(Membership);
admin.site.register(Community);