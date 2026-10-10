from django.shortcuts import render, redirect;
from django.contrib.auth import login, logout;
from django.contrib.auth.models import User;
from .models import Profile;
from .forms_stub import LoginForm, RegistrationForm;

# Create your views here.

def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST);
        
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
                email=form.cleaned_data['email']
            );

            Profile.objects.create(
                user=user
            );

            return redirect("accounts:login");
    else:
        form = RegistrationForm();

    return render(request, "accounts/register.html", {"form":form});

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST);

        if form.is_valid():
            user = form.get_user();
            login(request, user);

            return redirect("main:index");

    else:
        form = LoginForm(request);
    
    return render(request, 'accounts/login.html', {"form":form});

def logout_view(request):
    if request.method == "GET":
        logout(request);
    return redirect("accounts:login");
