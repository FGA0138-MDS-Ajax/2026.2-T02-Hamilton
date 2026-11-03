from django.forms import ModelForm;
from .models import Message, Forum;

class MessageForm(ModelForm):
    class Meta:
        model = Message;
        fields = ['content'];

class ForumForm(ModelForm):
    class Meta:
        model = Forum;
        fields = ['name', 'state'];