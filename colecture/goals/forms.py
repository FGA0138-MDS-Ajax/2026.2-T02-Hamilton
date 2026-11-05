from django import forms
from django.utils import timezone

from .models import GOAL_DESC_MAX_LENGTH, Goal, ReadingSession


class GoalForm(forms.ModelForm):
    deadline = forms.DateTimeField(
        label="Prazo",
        required=False,
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
        help_text="Opcional. Sem prazo, a meta fica aberta até ser concluída.",
    )

    class Meta:
        model = Goal
        # os donos NÃO estão aqui: não podem ser trocados por POST
        fields = [
            "name", "description", "goal_type", "target",
            "deadline", "book", "status",
        ]
        labels = {
            "name": "Nome da meta",
            "description": "Descrição",
            "goal_type": "Tipo de meta",
            "target": "Quantidade-alvo",
            "book": "Livro",
            "status": "Status",
        }
        help_texts = {
            "description": "Opcional. Explique o objetivo da meta.",
            "target": "Quantidade de páginas ou horas a atingir, conforme o tipo escolhido.",
            "book": "Opcional. Livro ao qual a meta se refere.",
        }
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "Ex.: Ler 1000 páginas em novembro",
            }),
            "description": forms.Textarea(attrs={
                "rows": 4,
                "maxlength": GOAL_DESC_MAX_LENGTH,
                "placeholder": "Descreva a meta (opcional)...",
            }),
            "target": forms.NumberInput(attrs={"placeholder": "Ex.: 1000"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.owner_community_id is not None:
            # meta de comunidade: o livro é sempre o da comunidade e é
            # atribuído em GoalService.create_goal, então o campo não aparece
            del self.fields["book"]
        else:
            # livro é opcional: a meta não quebra se ele for excluído
            self.fields["book"].required = False
            self.fields["book"].empty_label = "Nenhum livro"
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


class ReadingSessionForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is not None:
            self.instance.user = user

    class Meta:
        model = ReadingSession
        fields = ["book", "page_start", "page_end", "minute_count", "date"]