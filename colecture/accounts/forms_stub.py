from django import forms;
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm;

class LoginForm(AuthenticationForm):
    pass;

class RegistrationForm(UserCreationForm):
    pass;

