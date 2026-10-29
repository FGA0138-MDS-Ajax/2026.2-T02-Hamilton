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