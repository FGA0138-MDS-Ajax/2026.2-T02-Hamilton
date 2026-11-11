"""Popula o banco com dados de demonstração: usuários, comunidades, fórum e metas.

Uso:
    python manage.py seed_demo                    # cria os dados que ainda não existem
    python manage.py seed_demo --password abc123  # define outra senha para os usuários

O que é criado:
    - 5 usuários (ana, bruno, carla, diego, elisa), todos com Profile;
    - 2 comunidades: uma PÚBLICA e uma PRIVADA (com um pedido de entrada pendente);
    - mensagens no fórum geral de cada comunidade;
    - 1 meta coletiva por comunidade (com fórum automático) e 1 meta individual por usuário;
    - a usuária "ana" com 5 dias seguidos de leitura (ofensiva de 5 dias).

O comando é idempotente: rodá-lo de novo não duplica usuários, comunidades,
mensagens nem metas. Se o catálogo estiver vazio, o seed_books é executado antes.
"""
from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import Profile
from accounts.services import AccountService
from books.models import Book, ReadingSession
from books.services import persist_reading_session
from communities.models import Community, Membership
from communities.services import CommunityService, MembershipService
from forums.models import Message
from goals.models import Goal, GoalParticipation
from goals.services import GoalService

DEFAULT_PASSWORD = "Senha#123"

# Quantos dias as metas e participações "nascem" no passado, para que as
# leituras da ofensiva já contem no progresso delas.
BACKDATE_DAYS = 7

# ISBNs (vindos do seed_books) usados nas comunidades e metas.
ISBN_DUNE = "9780441172719"
ISBN_HOBBIT = "9780547928227"
ISBN_HARRY_POTTER = "9780590353427"

USERS = ["ana", "bruno", "carla", "diego", "elisa"]

# (autor, minutos atrás, texto)
PUBLIC_MESSAGES = [
    ("ana", 3000, "Bem-vindos ao clube! Nosso livro do mês é Duna. Quem já leu algo do Frank Herbert?"),
    ("bruno", 2900, "Eu li Duna há uns anos, mas vou reler com vocês. A construção de mundo é absurda."),
    ("carla", 2700, "Comecei ontem e já estou fascinada pela especiaria. Vamos combinar um ritmo de páginas por dia?"),
    ("diego", 2400, "Sugiro 30 páginas por dia, assim fechamos a meta do mês sem sufoco."),
    ("elisa", 1500, "Fechado! Vou registrar minha leitura todo dia para não perder a ofensiva 🔥"),
    ("ana", 600, "Cheguei ao capítulo em que o Paul encontra os Fremen. Sem spoilers, por favor!"),
    ("bruno", 120, "Prometo não dar spoiler. Quem quer abrir uma discussão sobre o Bene Gesserit depois?"),
]

PRIVATE_MESSAGES = [
    ("bruno", 2800, "Este círculo é fechado de propósito: só entra quem o moderador aprova."),
    ("carla", 2600, "Adorei a ideia. O Hobbit é perfeito para começar uma jornada de leitura em grupo."),
    ("diego", 1800, "Já estou na parte dos trolls. Bilbo é muito melhor personagem do que eu lembrava."),
    ("carla", 900, "Que tal discutirmos o capítulo do Gollum na sexta?"),
    ("bruno", 200, "Combinado. Quem estiver atrasado, sem pressa: o importante é manter o hábito."),
]

# Metas coletivas: (comunidade, nome, descrição, tipo, alvo, prazo em dias)
# Para HOUR_COUNT o alvo é em MINUTOS (600 = 10h).
COMMUNITY_GOALS = {
    "Clube da Ficção Científica": (
        "Ler 500 páginas de Duna juntos",
        "Meta coletiva: somar 500 páginas lidas por todos os membros em 30 dias.",
        Goal.GoalType.PAGE_COUNT, 500, 30,
    ),
    "Círculo dos Clássicos de Fantasia": (
        "10 horas de Hobbit em grupo",
        "Meta coletiva: somar 10 horas de leitura de O Hobbit em 21 dias.",
        Goal.GoalType.HOUR_COUNT, 600, 21,
    ),
}

# Metas individuais, uma por usuário: (nome, tipo, alvo, período, dias da semana, emoji, isbn)
INDIVIDUAL_GOALS = {
    "ana": ("Leitura diária", Goal.GoalType.PAGE_COUNT, 20, Goal.Period.DAILY, "", "🔥", None),
    "bruno": ("150 páginas por semana", Goal.GoalType.PAGE_COUNT, 150, Goal.Period.WEEKLY, "", "📚", None),
    "carla": ("30 minutos por dia", Goal.GoalType.HOUR_COUNT, 30, Goal.Period.DAILY, "", "⏱️", None),
    "diego": ("Leitura seg/qua/sex", Goal.GoalType.PAGE_COUNT, 30, Goal.Period.WEEKDAYS, "0,2,4", "🌙", None),
    "elisa": ("Terminar Harry Potter", Goal.GoalType.PAGE_COUNT, 309, Goal.Period.TOTAL, "", "📖", ISBN_HARRY_POTTER),
}

STREAK_USER = "ana"
STREAK_DAYS = 5          # dias seguidos, terminando hoje
STREAK_PAGES_PER_DAY = 30
STREAK_MINUTES_PER_DAY = 40


class Command(BaseCommand):
    help = (
        "Cria usuários, comunidades (uma pública e uma privada), mensagens de fórum, "
        "metas e uma ofensiva de demonstração. Uso: python manage.py seed_demo"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--password", default=DEFAULT_PASSWORD,
            help=f"Senha dos usuários criados (padrão: {DEFAULT_PASSWORD}).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        books = self._get_books()
        users = self._create_users(options["password"])
        public, private = self._create_communities(users, books)
        self._create_messages(public, private, users)
        self._create_community_goals()
        self._create_individual_goals(users, books)
        self._create_streak(users[STREAK_USER], books[ISBN_DUNE])

        self.stdout.write(self.style.SUCCESS("Dados de demonstração prontos."))
        self.stdout.write(f"  Usuários: {', '.join(USERS)} (senha: {options['password']})")
        self.stdout.write(f"  Comunidade pública:  {public.name} (código {public.code})")
        self.stdout.write(f"  Comunidade privada:  {private.name} (código {private.code})")
        profile = Profile.objects.get(user=users[STREAK_USER])
        self.stdout.write(f"  Ofensiva de {STREAK_USER}: {profile.streak} dia(s)")

    # ------------------------------------------------------------------
    def _get_books(self):
        isbns = [ISBN_DUNE, ISBN_HOBBIT, ISBN_HARRY_POTTER]
        if Book.objects.filter(isbn__in=isbns).count() < len(isbns):
            self.stdout.write("Catálogo incompleto: executando seed_books...")
            call_command("seed_books")
        books = {b.isbn: b for b in Book.objects.filter(isbn__in=isbns)}
        missing = [i for i in isbns if i not in books]
        if missing:
            raise CommandError(f"Livros não encontrados no catálogo: {', '.join(missing)}")
        return books

    def _create_users(self, password):
        User = get_user_model()
        users = {}
        for username in USERS:
            user = User.objects.filter(username=username).first()
            if user is None:
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@colecture.test",
                    password=password,
                )
                self.stdout.write(f"Usuário criado: {username}")
            # o Profile normalmente nasce no cadastro (AccountService)
            if not Profile.objects.filter(user=user).exists():
                AccountService.create_account(user)
            users[username] = user
        return users

    def _get_or_create_community(self, creator, name, description, access, book):
        community = Community.objects.filter(name=name).first()
        if community is not None:
            return community
        community = CommunityService.create_community(
            Community(name=name, description=description, access=access, book=book),
            creator=creator,
        )  # também cria o fórum geral
        self.stdout.write(f"Comunidade criada: {name} ({access})")
        return community

    def _create_communities(self, users, books):
        public = self._get_or_create_community(
            users["ana"],
            "Clube da Ficção Científica",
            "Comunidade aberta para quem ama ficção científica. Qualquer pessoa pode entrar.",
            Community.Access.PUBLIC,
            books[ISBN_DUNE],
        )
        private = self._get_or_create_community(
            users["bruno"],
            "Círculo dos Clássicos de Fantasia",
            "Comunidade fechada: a entrada depende da aprovação de um moderador.",
            Community.Access.PRIVATE,
            books[ISBN_HOBBIT],
        )

        # O criador não tem Membership (já conta como membro).
        M = Membership
        for username, role in [
            ("bruno", M.Role.MODERATOR), ("carla", M.Role.MEMBER),
            ("diego", M.Role.MEMBER), ("elisa", M.Role.MEMBER),
        ]:
            MembershipService.enter_community(users[username], public, role=role, status=M.Status.ACTIVE)

        for username, role in [("carla", M.Role.MODERATOR), ("diego", M.Role.MEMBER)]:
            MembershipService.enter_community(users[username], private, role=role, status=M.Status.ACTIVE)
        # pedido de entrada aguardando aprovação na comunidade privada
        MembershipService.enter_community(users["elisa"], private, role=M.Role.NONE, status=M.Status.PENDING)

        return public, private

    def _create_messages(self, public, private, users):
        now = timezone.now()
        for community, messages in ((public, PUBLIC_MESSAGES), (private, PRIVATE_MESSAGES)):
            forum = community.forum  # fórum geral, criado junto com a comunidade
            for username, minutes_ago, content in messages:
                if Message.objects.filter(forum=forum, content=content).exists():
                    continue
                message = Message.objects.create(forum=forum, author=users[username], content=content)
                # created_at é auto_now_add: ajusta depois para espalhar as mensagens no tempo
                Message.objects.filter(pk=message.pk).update(
                    created_at=now - timedelta(minutes=minutes_ago)
                )

    def _create_community_goals(self):
        backdate = timezone.now() - timedelta(days=BACKDATE_DAYS)
        for community_name, (name, description, goal_type, target, days) in COMMUNITY_GOALS.items():
            community = Community.objects.get(name=community_name)
            if Goal.objects.filter(owner_community=community, name=name).exists():
                continue
            goal = GoalService.create_goal(
                Goal(
                    name=name,
                    description=description,
                    owner_community=community,
                    goal_type=goal_type,
                    target=target,
                    deadline=timezone.now() + timedelta(days=days),
                    period=Goal.Period.TOTAL,
                ),
                creator=community.creator,
            )  # cria o fórum da meta e inscreve todos os membros
            self._backdate_goal(goal, backdate)
            self.stdout.write(f"Meta coletiva criada: {name}")

    def _create_individual_goals(self, users, books):
        backdate = timezone.now() - timedelta(days=BACKDATE_DAYS)
        for username, (name, goal_type, target, period, weekdays, emoji, isbn) in INDIVIDUAL_GOALS.items():
            user = users[username]
            profile = Profile.objects.get(user=user)
            if Goal.objects.filter(owner_profile=profile, name=name).exists():
                continue
            goal = GoalService.create_goal(
                Goal(
                    name=name,
                    owner_profile=profile,
                    goal_type=goal_type,
                    target=target,
                    period=period,
                    weekdays=weekdays,
                    emoji=emoji,
                    book=books[isbn] if isbn else None,
                ),
                creator=user,
            )
            self._backdate_goal(goal, backdate)
            self.stdout.write(f"Meta individual criada: {username} - {name}")

    @staticmethod
    def _backdate_goal(goal, moment):
        """Recua a criação da meta e as entradas nela (campos auto/now no create)."""
        Goal.objects.filter(pk=goal.pk).update(created_at=moment)
        GoalParticipation.objects.filter(goal=goal).update(joined_at=moment)

    def _create_streak(self, user, book):
        """Registra STREAK_DAYS dias seguidos de leitura (terminando hoje).

        Usa persist_reading_session, o mesmo serviço da tela "Registrar leitura",
        que atualiza o BookStatus e a ofensiva do Profile.
        """
        if ReadingSession.objects.filter(user=user).exists():
            return  # já tem leituras: não duplica
        today = timezone.localdate()
        for offset in range(STREAK_DAYS - 1, -1, -1):  # do dia mais antigo até hoje
            day = today - timedelta(days=offset)
            if offset == 0:
                created_at = timezone.now() - timedelta(minutes=1)
            else:
                created_at = timezone.make_aware(datetime.combine(day, time(20, 0)))
            persist_reading_session(user, book, {
                "record_type": ReadingSession.RecordType.PAGES,
                "pages_read": STREAK_PAGES_PER_DAY,
                "stopped_percent": None,
                "minute_count": STREAK_MINUTES_PER_DAY,
                "created_at": created_at,
            })
        self.stdout.write(f"Ofensiva criada: {user.username} com {STREAK_DAYS} dias de leitura")
