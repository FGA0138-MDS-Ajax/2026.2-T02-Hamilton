from django.shortcuts import render, redirect;
from django.contrib.auth import login, logout, get_user_model;
from django.contrib.auth.decorators import login_required;
from django.contrib import messages
from .models import Profile;
from .forms import LoginForm, RegistrationForm, EditUserForm;

def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST);
        
        if form.is_valid():
            user = get_user_model().objects.create_user(
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

            # pega a URL que o usuário tentava acessar antes do login.
            next_url = request.POST.get('next') or request.GET.get('next');

            return redirect(next_url or "main:index");
        else:
            # Mensagem de erro ao falhar no login
            messages.error(request, 'Usuário ou senha inválidos. Tente novamente.')

    else:
        form = LoginForm(request);
    
    return render(request, 'accounts/login.html', {"form":form});

def logout_view(request):
    if request.method == "POST":
        logout(request);
    return redirect("main:index");

@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, 'accounts/profile.html', {'profile': profile})

@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = EditUserForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('accounts:profile')
    else:
        form = EditUserForm(instance=request.user)

    return render(request, 'accounts/profileEdit.html', {'editForm': form})
