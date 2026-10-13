from django.shortcuts import render, redirect;
from django.contrib.auth import login, logout, get_user_model;
from .models import Profile;
from .forms import LoginForm, RegistrationForm;

# Create your views here.

def register_view(request):
    if request.method == "POST": # verifica se o usuário está enviando informações
        form = RegistrationForm(request.POST); # manda essas informações para o formulário que irá validá-las.
        
        if form.is_valid(): # todas as informações são válidas.
            user = get_user_model().objects.create_user( # cria o usuário
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
                email=form.cleaned_data['email']
            );

            Profile.objects.create( # cria o profile que sediará o usuário
                user=user
            );

            return redirect("accounts:login"); # redireciona para a página de login
    else:
        """
        Neste caso o usuário está entrando na página agora então
        criamos um formulário vazio para que possa preenchê-lo.
        """
        form = RegistrationForm();

    return render(request, "accounts/register.html", {"form":form});

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST);

        if form.is_valid():
            user = form.get_user(); # pega o usuário utilizando as informações do formulário.
            login(request, user); # faz o login nativo do Django.

            return redirect("main:index"); # redireciona para a página inicial.

    else:
        form = LoginForm(request);
    
    return render(request, 'accounts/login.html', {"form":form});

def logout_view(request):
    if request.method == "POST": # aceita apenas requests com método POST
        logout(request); # faz o logout nativo do Django
    return redirect("main:index"); # redireciona para a main página novamente

def profile_view(request):
    if request.user.is_authenticated:
        return render(request, 'accounts/profile.html')
    return render(request, 'main/index.html')