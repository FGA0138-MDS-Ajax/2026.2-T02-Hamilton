from django.shortcuts import render, redirect;
from django.contrib.auth import login, logout;
from django.contrib.auth.models import User;
from .forms_stub import LoginForm, RegistrationForm;

# Create your views here.

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
