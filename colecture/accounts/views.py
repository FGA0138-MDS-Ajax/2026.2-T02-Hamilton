from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model;
from django.contrib.auth.decorators import login_required;
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from django.http import Http404

from datetime import date, timedelta
import calendar

from .models import Profile;
from goals.services import GoalService;
from .services import AccountService;
from .forms import LoginForm, RegistrationForm, EditUserForm;

from books.models import BookStatus, ReadingSession

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
    
    individual_goal = GoalService.get_current_individual_goal(profile)
    goal_progress = (
        GoalService.get_individual_progress(individual_goal) if individual_goal else None
    )
    
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
        'goal_progress': goal_progress,
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



@login_required
def streak_calendar_view(request):
    """
    Exibe o calendário de ofensivas do usuário autenticado.
    Os dias destacados são aqueles que possuem sessões de leitura.
    """

    today = timezone.localdate()

    # Recupera o mês solicitado pela URL (?month=AAAA-MM).
    month_param = request.GET.get('month')

    try:
        if month_param:
            year, month = map(int, month_param.split('-'))
            first_day = date(year, month, 1)
        else:
            first_day = today.replace(day=1)
    except (ValueError, TypeError):
        first_day = today.replace(day=1)

    # Último dia do mês.
    last_day_number = calendar.monthrange(
        first_day.year,
        first_day.month
    )[1]

    last_day = first_day.replace(day=last_day_number)

    # Dias que possuem sessões de leitura.
    reading_days = set(
        ReadingSession.objects.filter(
            user=request.user,
            date__gte=first_day,
            date__lte=last_day
        ).values_list('date', flat=True).distinct()
    )

    # Calendário começando no domingo.
    cal = calendar.Calendar(firstweekday=6)

    weeks = cal.monthdayscalendar(
        first_day.year,
        first_day.month
    )

    calendar_weeks = []

    for week in weeks:
        calendar_week = []

        for day_number in week:
            if day_number == 0:
                calendar_week.append(None)
                continue

            current_date = first_day.replace(day=day_number)

            calendar_week.append({
                'number': day_number,
                'date': current_date,
                'has_reading': current_date in reading_days,
                'is_today': current_date == today,
                'is_future': current_date > today,
            })

        calendar_weeks.append(calendar_week)

    # Navegação entre os meses.
    previous_month = (
        first_day - timedelta(days=1)
    ).replace(day=1)

    next_month = (
        last_day + timedelta(days=1)
    ).replace(day=1)

    month_names = [
        '',
        'Janeiro', 'Fevereiro', 'Março', 'Abril',
        'Maio', 'Junho', 'Julho', 'Agosto',
        'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]

    context = {
        'weeks': calendar_weeks,
        'today': today,
        'month_name': month_names[first_day.month],
        'year': first_day.year,
        'previous_month': previous_month.strftime('%Y-%m'),
        'next_month': next_month.strftime('%Y-%m'),
    }

    return render(
        request,
        'accounts/streak_calendar.html',
        context
    )


@login_required
def streak_day_history_view(request, day):
    """
    Exibe o histórico de leitura do usuário em um dia específico.
    """
    try:
        selected_date = date.fromisoformat(day)
    except ValueError:
        raise Http404("Data inválida.")

    if selected_date > timezone.localdate():
        raise Http404("Não é possível consultar uma data futura.")

    sessions = (
        ReadingSession.objects
        .filter(user=request.user, date=selected_date)
        .select_related('book')
        .order_by('book__title', 'pk')
    )

    totals = sessions.aggregate(
        total_pages=Sum('pages_read'),
        total_minutes=Sum('minute_count')
    )

    context = {
        'selected_date': selected_date,
        'sessions': sessions,
        'total_sessions': sessions.count(),
        'total_pages': totals['total_pages'] or 0,
        'total_minutes': totals['total_minutes'] or 0,
        'has_sessions': sessions.exists(),
    }

    return render(
        request,
        'accounts/streak_day_history.html',
        context
    )