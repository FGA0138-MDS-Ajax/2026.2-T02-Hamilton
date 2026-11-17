from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Somente leitura: editar e excluir logs é feito pelas views do app
    (/logs/), que registram essas ações no próprio log de auditoria. O painel
    do Django não faria esse registro."""

    list_display = ("id", "action", "actor", "content_type", "object_id", "created_at")
    list_filter = ("action", "content_type")
    search_fields = ("actor__username", "object_id")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
