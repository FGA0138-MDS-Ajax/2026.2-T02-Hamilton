from books.models import BookStatus, ReadingSession
from rewards.models import Award, Insignia
from rewards.models import Insignia, Award, CriteriaType
from django.db.models import Sum
from goals.models import Goal, GoalParticipation
from django.utils import timezone
from goals.services import GoalService

# Confere primeiro livro lido
def check_first_read(user):
    # Verifica se existe alguma sessão de leitura registrada
    has_session = ReadingSession.objects.filter(
        user=user
        ).exists()
    
    # Verifica se há progresso registrado em algum livro
    has_progress = BookStatus.objects.filter(
        user=user,
        reading_progress__gt=0
    ).exists()

# Retorna falso se o usuário não iniciou nenhuma leitura
    if not (has_session or has_progress):
        return False

# Busca a insígnia ativa correspondente ao primeira leitura
    insignia = Insignia.objects.filter(
        name ='Primeira Faísca',
        is_active=True
    ).first()


    if insignia is None:
        return False
     
     # Atribui a insígnia ao usuário
    _, created = Award.objects.get_or_create(
        user=user,
        insignia=insignia
    )
    
    return created


# Confere os livros lidos
def check_books_read(user):
    # Conta quantos livros o usuário marcou como lidos
    books_read = BookStatus.objects.filter(
        user=user,
        status=BookStatus.Status.READ
    ).count()

# Busca insígnias ativas que correspondem à quantidade de livros lidos
    achievements = Insignia.objects.filter(
        criteria_type=CriteriaType.BOOKS_READ,
        criteria_value__lte=books_read,
        is_active=True
    )

    awarded = False
    
# Concede cada insígnia adquirida ao usuário
    for insignia in achievements:
        _, created = Award.objects.get_or_create(
            user=user,
            insignia=insignia
        )

        if created:
            awarded = True

    return awarded

# Confere quantidade de generos li  dos
def check_genres_read(user):
# Conta a quantidade de gêneros literários distintos nos livros lidos
    genres_read = (
        BookStatus.objects
        .filter(
            user=user,
            status=BookStatus.Status.READ
        )
        .exclude(book__genre='')
        .values('book__genre')
        .distinct()
        .count()
    )

# Filtra insígnias de categorias de livros com base nos gêneros 
    achievements = Insignia.objects.filter(
        criteria_type=CriteriaType.BOOKS_READ,
        criteria_value__lte=genres_read,
        is_active=True,
        name='Explorador de Gêneros'
    )

    awarded = False

# Atribui as insígnias conquistadas
    for insignia in achievements:
        _, created = Award.objects.get_or_create(
            user=user,
            insignia=insignia
        )

        if created:
            awarded = True

    return awarded

# Confere streak do usuario
def check_streak(user):
    profile = user.profile

# Busca insígnias baseadas na ofensiva (streak)
    achievements = Insignia.objects.filter(
        criteria_type=CriteriaType.STREAK,
        criteria_value__lte=profile.streak,
        is_active=True
    )
    
# Concede as insígnias de streak 
    for insignia in achievements:
        Award.objects.get_or_create(
            user=user,
            insignia=insignia
        )
        
# Confere paginas lida em um unico dia
def check_daily_pages(user):
    # Caulcula o número de páginas lido em um dia
    daily_pages = (
        ReadingSession.objects
        .filter(user=user)
        .values('date')
        .annotate(total_pages=Sum('pages_read'))
        .order_by('-total_pages')
        .first()
    )

    if daily_pages is None:
        return False

# Exige um mínimo de 100 páginas em um único dia para validar
    if daily_pages['total_pages'] < 100:
        return False

# Busca a insígnia específica de maratonista de páginas
    insignia = Insignia.objects.filter(
        name='Maratonista',
        criteria_type=CriteriaType.DAILY_PROGRESS,
        criteria_value__lte=daily_pages['total_pages'],
        is_active=True
    ).first()

    if insignia is None:
        return False

    _, created = Award.objects.get_or_create(
        user=user,
        insignia=insignia
    )

    return created

# Confere o total de paginas lidas
def check_total_pages(user):
    # Soma todas as páginas lidas em todas as sessões do usuário
    total_pages = ReadingSession.objects.filter(
        user=user,
    ).aggregate(total=Sum('pages_read'))['total'] or 0

# Busca insígnias por volume total de páginas, excluindo a de maratonista diário
    achievements = Insignia.objects.filter(
        criteria_type = CriteriaType.DAILY_PROGRESS,
        criteria_value__lte=total_pages,
    ).exclude(name='Maratonista')

    awarded = False
# Atribui as insígnias alcançadas
    for insignia in achievements:
        _, created = Award.objects.get_or_create(
            user=user,
            insignia=insignia
       )

        if created:
            awarded = True
    return awarded

# Confere o total de tempo  (minutos) lido em um dia
def check_daily_minutes(user):
    # Agrupa o tempo de leitura em um unico dia
    daily_minutes = (
        ReadingSession.objects
        .filter(user=user)
        .values('date')
        .annotate(total_minutes=Sum('minute_count'))
        .order_by('-total_minutes')
        .first()
    )

    if daily_minutes is None:
       return False
# Busca a insígnia de para o tempo diário atingido
    insignia = Insignia.objects.filter(
        name ='Leitura Profunda',
        criteria_type=CriteriaType.HOURS_READ,
        criteria_value__lte=daily_minutes['total_minutes'],
        is_active=True
    ).first()

    if insignia is None:
        return False
    _,created = Award.objects.get_or_create(
        user=user,
        insignia=insignia
    )
    
    return created


# Confere o total de tempo  (minutos) acumulativo lido
def check_total_minutes(user):
    # Soma todos os minutos de leitura do usuário
    total_minutes = ReadingSession.objects.filter(
        user=user
    ).aggregate(total=Sum('minute_count'))['total'] or 0
    
    # Busca insígnias de tempo acumulado, ignorando a regra de diárias
    achievements = Insignia.objects.filter(
        criteria_type=CriteriaType.HOURS_READ,
        criteria_value__lte=total_minutes,
        is_active=True
    ).exclude(name='Leitura Profunda')
    
    awarded = False
    
    # Concede as insígnias desbloqueadas
    for insignia in achievements:
        _,created = Award.objects.get_or_create(
            user=user,
            insignia=insignia
        )
        
        if created:
            awarded = True
            
    return awarded

# Confere se o usuario criou uma meta
def check_individual_goal_created(user):
    # Conta quantas metas individuais o usuário criou (sem incluir metas de comunidade)
    goals_created = Goal.objects.filter(
        owner_profile__user=user,
        owner_community__isnull=True
    ).count()
    
    if goals_created <1:
        return False
    
    # Busca a insígnia de criação da primeira meta
    insignia = Insignia.objects.filter(
        name='Primeiro Plano',
        criteria_type= CriteriaType.INDIVIDUAL_GOAL,
        is_active=True
    ).first()
    
    if insignia is None:
        return False
    
    _,created = Award.objects.get_or_create(
        user=user,
        insignia=insignia
    )
    return created

# Confere conclusão de metas individuais

def check_individual_goals_completed(user):
    # Conta quantas metas individuais o usuário concluiu com sucesso
    goals_completed = Goal.objects.filter(
        owner_profile__user=user,
        owner_community__isnull=True,
        status=Goal.Status.CONCLUDED
    ).count()
    
    # Busca insígnias de metas concluídas, ignorando insígnias iniciais específicas
    achievements = Insignia.objects.filter(
        criteria_type=CriteriaType.INDIVIDUAL_GOAL,
        criteria_value__lte=goals_completed,
        is_active=True
    ).exclude(
        name__in=['Primeiro Plano', 'No Prazo Certo']
    )
    
    awarded = False
    
    # Atribui as insígnias conquistadas
    for insignia in achievements:
        _, created = Award.objects.get_or_create(
            user=user,
            insignia=insignia
        )
        
        if created:
            awarded = True
            
    return awarded

# Confere se Concluiu uma meta individual antes da data limite 
def check_individual_goal_on_time(goal):
    
    # Garante que a meta tem um dono e uma data limite
    if goal.owner_profile_id is None or goal.deadline is None:
        return False
    
    # Retorna falso se o momento atual já passou da data limite da met
    if timezone.now() > goal.deadline:
        return False
    
    # Busca a insígnia ativa relacionada a cumprir metas no prazo
    insignia = Insignia.objects.filter(
        name='No Prazo Certo',
        criteria_type=CriteriaType.INDIVIDUAL_GOAL,
        is_active=True
    ).first()
    
    if insignia is None:
        return False
    
    # Concede a insígnia ao usuário dono da meta
    _, created = Award.objects.get_or_create(
        user=goal.owner_profile.user,
        insignia=insignia
    )
    
    return created

# Confere metas da comunidade comcluidos
def check_community_goals_completed(user):
    
    # Busca as participações do usuário em metas vinculadas a comunidades
    participations = GoalParticipation.objects.filter(
        user=user,
        goal__owner_community__isnull=False
    ).select_related('goal','goal__book')
    
    # Conta quantas metas o usuário concluiu 
    completed_count = 0

    for participation in participations:
        contribution = GoalService.get_user_contribution(participation)

        if contribution >= participation.goal.target:
            completed_count += 1
            from rewards.services import (
                check_community_goal_on_time)
            check_community_goal_on_time(participation)
    
    # Busca insígnias ativas de metas de comunidade alcançadas
    achievements = Insignia.objects.filter(
        criteria_type=CriteriaType.COMMUNITY_GOAL,
        criteria_value__lte=completed_count,
        is_active=True
    ).exclude(
        name__in=['Pontual','Fundador']
    )
    
    awarded = False
    
    # Concede as insígnias conquistadas ao usuário
    for insignia in achievements:
        _, created = Award.objects.get_or_create(
            user=user,
            insignia=insignia
        )
        
        if created:
            awarded = True
            
    return awarded

# Confere se Concluiu uma meta da comunidade antes da data limite  
def check_community_goal_on_time(participation):
    goal = participation.goal
    
# Retorna falso se a meta não for coletiva ou não tiver prazo definido
    if not goal.is_collective or goal.deadline is None:
        return False
    
    # Filtra as sessões de leitura dentro do prazo válido
    sessions = ReadingSession.objects.filter(
        user=participation.user,
        created_at__gte=participation.joined_at,
        created_at__lte=goal.deadline
        )
    
    # Se a meta for focada em um livro específico, filtra as sessões apenas desse livro
    if goal.book_id:
        sessions = sessions.filter(
            book_id=goal.book_id
        )
    # Calcula o progresso total dependendo do tipo da meta (páginas ou minutos/horas)
    if goal.goal_type == Goal.GoalType.PAGE_COUNT:
        total = sessions.filter(
            pages_read__isnull=False
        ).aggregate(total=Sum('pages_read'))['total'] or 0    
        
    elif goal.goal_type == Goal.GoalType.HOUR_COUNT:
        total = sessions.aggregate(
                total=Sum('minute_count')
            )['total'] or 0
        
    else:
        return False

# Se o total lido for menor que a meta exigida, retorna false
    if total < goal.target:
        return False
    
# Busca a insígnia relacionada à conclusão de meta de comunidade no prazo    
    insignia = Insignia.objects.filter(
       name ='Pontual',
       criteria_type=CriteriaType.COMMUNITY_GOAL,
       is_active=True
   ).first()
    
    if insignia is None:
        return False
    
    # Concede a insígnia ao usuário 
    _, created = Award.objects.get_or_create(
            user=participation.user,
            insignia=insignia
        )
    
    return created
        
def check_community_founder(user):
    from communities.models import Community, Membership
    
    insignia = Insignia.objects.filter(
        name='Fundador',
        criteria_type=CriteriaType.COMMUNITY,
        is_active=True
    ).first()
    
    if insignia is None:
        return False
    
    created_community = Community.objects.filter(
        creator=user
    ).exists()
    
    is_moderador = Membership.objects.filter(
            user=user,
            role=Membership.Role.MODERATOR,
            status=Membership.Status.ACTIVE
        ).exists()
    
    
    if not(created_community or is_moderador):
        return False
    
    
    _, created = Award.objects.get_or_create(
        user=user,
        insignia=insignia
    )
    
    return created

