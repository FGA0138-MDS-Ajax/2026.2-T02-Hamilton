from django import forms
from django.contrib.contenttypes.models import ContentType

from .models import AuditLog


class AuditLogForm(forms.ModelForm):
    """Edição de um log por um administrador."""

    class Meta:
        model = AuditLog
        fields = ["actor", "action", "content_type", "object_id", "metadata"]

    def clean_metadata(self):
        metadata = self.cleaned_data.get("metadata")
        # o metadata é sempre um objeto JSON ({...}); vazio vira {}
        if metadata in (None, ""):
            return {}
        if not isinstance(metadata, dict):
            raise forms.ValidationError("O metadata precisa ser um objeto JSON (ex.: {\"chave\": \"valor\"}).")
        return metadata


class AuditLogFilterForm(forms.Form):
    """Filtros da listagem de logs (todos opcionais, enviados por GET)."""

    action = forms.ChoiceField(
        required=False,
        choices=[("", "Todas as ações")] + AuditLog.Action.choices,
    )
    actor = forms.CharField(required=False, max_length=150)
    content_type = forms.ModelChoiceField(
        required=False,
        queryset=ContentType.objects.none(),
        empty_label="Todas as classes",
    )
    object_id = forms.IntegerField(required=False, min_value=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # só as classes que já aparecem em algum log
        self.fields["content_type"].queryset = ContentType.objects.filter(
            id__in=AuditLog.objects.values("content_type")
        ).order_by("app_label", "model")

    def filter(self, queryset):
        """Aplica os filtros válidos ao queryset de logs."""
        # filtro inválido (ex.: ID não numérico): não mostra resultados
        # que pareçam ter sido filtrados quando não foram
        if not self.is_valid():
            return queryset.none()
        data = self.cleaned_data
        if data["action"]:
            queryset = queryset.filter(action=data["action"])
        if data["actor"]:
            queryset = queryset.filter(actor__username__icontains=data["actor"])
        if data["content_type"]:
            queryset = queryset.filter(content_type=data["content_type"])
        if data["object_id"] is not None:
            queryset = queryset.filter(object_id=data["object_id"])
        return queryset
