from django import forms
from django.forms import ModelForm
from .models import Message, Forum

class MessageForm(ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'reply_to']
        widgets = {
            'reply_to': forms.HiddenInput(attrs={'id': 'replyToInput'}),
        }

    def __init__(self, *args, forum=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.forum = forum
        if forum is not None:
            self.instance.forum = forum
            self.fields['reply_to'].queryset = Message.objects.filter(forum=forum)
        self.fields['reply_to'].required = False

    def clean(self):
        cleaned_data = super().clean()
        reply_to = cleaned_data.get('reply_to')
        if reply_to and self.forum and reply_to.forum_id != self.forum.id:
            self.add_error('reply_to', 'A mensagem respondida deve pertencer ao mesmo fórum.')
        return cleaned_data

class ForumForm(ModelForm):
    class Meta:
        model = Forum
        fields = ['name', 'state']
