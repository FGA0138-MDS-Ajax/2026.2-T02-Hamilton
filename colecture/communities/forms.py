from django import forms
from .models import Community

class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ["name", "description", "access", "state"]  # + "book" se existir no model

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # não aparece no formulário de criação; usa o default do model
        self.fields["state"].required = False