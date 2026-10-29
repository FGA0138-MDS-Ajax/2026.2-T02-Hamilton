from django import forms
from .models import Community

class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ["name", "description", "access", "state", "book"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # não aparece no formulário de criação; usa o default do model
        self.fields["state"].required = False
        # livro é opcional: a comunidade não quebra se ele for excluído
        self.fields["book"].required = False

    def clean_state(self):
        state = self.cleaned_data.get("state")
        if not state:
            # na edição o estado é obrigatório; sem esta checagem, um "state"
            # vazio passava na validação e era salvo como string vazia.
            if self.instance.pk:
                raise forms.ValidationError("Informe o estado da comunidade.")
            # na criação o campo nem aparece no formulário: usa o padrão
            return Community.State.ACTIVE
        return state