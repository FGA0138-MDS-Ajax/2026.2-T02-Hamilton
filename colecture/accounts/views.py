from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model;
from django.contrib.auth.decorators import login_required;
from django.contrib import messages
from django.utils import timezone
from .models import Profile;
from books.models import BookStatus;
from .services import AccountService;
from .forms import LoginForm, RegistrationForm, EditUserForm;

def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST);
        
        if form.is_valid():
            user = AccountService.create_account(
                get_user_model().objects.create_user(
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password1'],
                    email=form.cleaned_data['email']
                )
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

            next_url = request.POST.get('next') or request.GET.get('next');

            return redirect(next_url or "main:index");
        else:
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
    
    # Busca a meta individual ativa do usuário (caso exista o model IndividualGoal ou similar)
    individual_goal = getattr(profile, 'individual_goal', None)
    
    # Verifica se leu hoje (exemplo integrando com ReadingLog se houver)
    today = timezone.localdate()
    read_today = False
    if hasattr(profile, 'reading_logs'):
        read_today = profile.reading_logs.filter(date=today).exists()

    # Estante: livros do usuário com a tag (Lido, Lendo, Quero ler)
    shelf_items = list(
        BookStatus.objects
        .filter(user=request.user)
        .select_related('book')
        .order_by('book__title')
    )

    counts = {choice: 0 for choice in BookStatus.Status.values}
    for item in shelf_items:
        counts[item.status] += 1

    # Ordem do filtro (F01): Todos, Lido, Lendo, Quero ler
    shelf_filters = [
        {'value': 'ALL', 'label': 'Todos', 'icon': 'bx-library', 'count': len(shelf_items)},
    ] + [
        {'value': value, 'label': BookStatus.Status(value).label, 'icon': icon, 'count': counts[value]}
        for value, icon in (
            (BookStatus.Status.READ, 'bxs-bookmark-alt'),
            (BookStatus.Status.READING, 'bxs-bookmark-minus'),
            (BookStatus.Status.WANT_TO_READ, 'bxs-bookmark-plus'),
        )
    ]

    context = {
        'profile': profile,
        'individual_goal': individual_goal,
        'read_today': read_today,
        'shelf_items': shelf_items,
        'shelf_filters': shelf_filters,
    }
    return render(request, 'accounts/profile.html', context)

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