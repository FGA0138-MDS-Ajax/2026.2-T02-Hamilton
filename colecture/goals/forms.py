from django import forms
from django.utils import timezone

from .models import Goal


class GoalForm(forms.ModelForm):
    deadline = forms.DateTimeField(
        required=False,
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
    )

    class Meta:
        model = Goal
        # os donos NÃO estão aqui: não podem ser trocados por POST
        fields = ["name", "goal_type", "target", "deadline", "book", "status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # livro é opcional: a meta não quebra se ele for excluído
        self.fields["book"].required = False
        # na criação o status é sempre ACTIVE (default do model)
        if not self.instance.pk:
            del self.fields["status"]

    def clean_deadline(self):
        deadline = self.cleaned_data.get("deadline")
        # só valida "futuro" se o prazo foi enviado/alterado; assim editar
        # outros campos de uma meta com prazo já vencido não é bloqueado
        if deadline and "deadline" in self.changed_data and deadline <= timezone.now():
            raise forms.ValidationError("O prazo deve estar no futuro.")
        return deadline
