from django import forms;
from django.contrib.auth.models import User;
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm;

DUPLICATE_EMAILS = False;

class LoginForm(AuthenticationForm):
    pass;

class RegistrationForm(UserCreationForm):
    email = forms.EmailField();

    def clean_email(self):
        email = self.cleaned_data['email'];
        if DUPLICATE_EMAILS:
            return email;

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "Um usuário com esse email já existe."
            );
    
        return email;
            
        
