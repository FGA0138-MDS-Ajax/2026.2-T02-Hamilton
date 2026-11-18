"""
Consultas de leitura das insígnias, usadas pelo perfil e pela página de insígnias.

Monta o contexto que os templates recebem: as insígnias ativas agrupadas por
categoria, marcando quais o usuário já conquistou (e quando).
"""
from django.contrib.staticfiles import finders
from django.core.exceptions import SuspiciousFileOperation
from django.templatetags.static import static
from django.utils.text import slugify

from .models import Award, CriteriaType, Insignia


# Numeração oficial da Ata da Reunião 07. O back identifica as insígnias pelo
# nome, então o número é mapeado pelo nome. A 18 (Madrugador das Letras) não
# foi aprovada e não existe no sistema.
INSIGNIA_NUMBERS = {
    'Primeira Faísca': 1,
    'Chama Acesa': 2,
    'Semana em Brasa': 3,
    'Quinzena Acesa': 4,
    'Fogueira Literária': 5,
    'Incêndio de Páginas': 6,
    'Meio Ano em Chamas': 7,
    'Chama Eterna': 8,
    'Primeira Página Virada': 9,
    'Leitor em Formação': 10,
    'Estante Crescendo': 11,
    'Biblioteca Ambulante': 12,
    'Guardião da Estante': 13,
    'Explorador de Gêneros': 14,
    'Maratonista': 15,
    'Mil Páginas': 16,
    'Dez Mil Páginas': 17,
    'Primeira Hora': 19,
    'Leitura Profunda': 20,
    'Dez Horas de Viagem': 21,
    'Cinquenta Horas': 22,
    'Centenário das Letras': 23,
    'Senhor do Tempo': 24,
    'Primeiro Plano': 25,
    'Missão Cumprida': 26,
    'No Prazo Certo': 27,
    'Determinação': 28,
    'Mestre das Metas': 29,
    'Primeiro Ciclo': 30,
    'Pontual': 31,
    'Veterano de Ciclos': 32,
    'Fundador': 33,
    'Primeira Opinião': 34,
    'Crítico Literário': 35,
    'Fênix': 36,
}

# Pasta das artes (Issue 1). Nome do arquivo: insignia-NN-nome-em-slug.svg
# ex.: insignia-01-primeira-faisca.svg
STATIC_ICON_DIR = 'rewards/img/insignias'

# Na ata, "Fundador" (tipo COMMUNITY no back) aparece em "Metas de comunidade".
DISPLAY_CATEGORY = {
    CriteriaType.COMMUNITY: CriteriaType.COMMUNITY_GOAL,
}


# Tema visual de cada categoria (R19 / Reunião 07).
# `slug` vira a classe CSS (cores em variables.css: --cat-<slug>) e
# `icon` é o ícone Boxicons usado enquanto a insígnia não tiver arte própria.
CATEGORY_STYLES = {
    CriteriaType.STREAK: {'slug': 'streak', 'icon': 'bxs-hot'},
    CriteriaType.BOOKS_READ: {'slug': 'books', 'icon': 'bxs-book'},
    CriteriaType.DAILY_PROGRESS: {'slug': 'pages', 'icon': 'bxs-file'},
    CriteriaType.HOURS_READ: {'slug': 'hours', 'icon': 'bxs-hourglass'},
    CriteriaType.INDIVIDUAL_GOAL: {'slug': 'goal', 'icon': 'bxs-flag-alt'},
    CriteriaType.COMMUNITY: {'slug': 'community', 'icon': 'bxs-group'},
    CriteriaType.COMMUNITY_GOAL: {'slug': 'community-goal', 'icon': 'bx-sync'},
    CriteriaType.SOCIAL: {'slug': 'social', 'icon': 'bxs-message-rounded-dots'},
    CriteriaType.SPECIAL: {'slug': 'special', 'icon': 'bxs-crown'},
}

DEFAULT_STYLE = {'slug': 'special', 'icon': 'bxs-award'}


def _static_icon_url(number, name):
    """Arte em static/rewards/img/insignias/ (SVG ou PNG), se existir."""
    if number is None:
        return None

    base = f'{STATIC_ICON_DIR}/insignia-{number:02d}-{slugify(name)}'
    for ext in ('svg', 'png'):
        path = f'{base}.{ext}'
        if finders.find(path):
            return static(path)
    return None


def _uploaded_icon_url(insignia):
    """
    Arte enviada pelo campo `icon` (media/), ou None se ainda não houver
    arquivo válido (o seed usa 'icon/' como valor provisório).
    """
    name = (insignia.icon.name or '').lstrip('/')
    if not name or name.endswith('/'):
        return None

    storage = insignia.icon.storage
    try:
        if not storage.exists(name):
            return None
        return storage.url(name)
    except (SuspiciousFileOperation, ValueError):
        return None


def _icon_url(insignia, number):
    # Prioridade: arte do repositório > upload no admin > ícone da categoria
    return _static_icon_url(number, insignia.name) or _uploaded_icon_url(insignia)


def get_insignia_overview(user, recent_limit=4):
    """
    Retorna:
        categories   -> lista de {label, slug, icon, items, earned_count, total_count}
        earned_count -> quantas insígnias o usuário conquistou
        total_count  -> quantas insígnias ativas existem
        percent      -> progresso geral (0 a 100)
        recent       -> últimas `recent_limit` insígnias conquistadas
    """
    # Ordem da ata; insígnias novas (sem número) vão para o fim
    insignias = sorted(
        Insignia.objects.filter(is_active=True),
        key=lambda i: (INSIGNIA_NUMBERS.get(i.name, 999), i.pk),
    )

    # Primeira data em que cada insígnia foi conquistada
    awarded_at = {}
    award_ids = {}
    awards = (
        Award.objects
        .filter(user=user, insignia__is_active=True)
        .order_by('awarded_at')
    )
    for award in awards:
        awarded_at.setdefault(award.insignia_id, award.awarded_at)
        award_ids.setdefault(award.insignia_id, award.id)

    by_type = {}
    earned_items = []

    for insignia in insignias:
        category = DISPLAY_CATEGORY.get(insignia.criteria_type, insignia.criteria_type)
        style = CATEGORY_STYLES.get(category, DEFAULT_STYLE)
        earned_date = awarded_at.get(insignia.pk)
        number = INSIGNIA_NUMBERS.get(insignia.name)

        item = {
            'id': insignia.pk,
            'number': number,
            'name': insignia.name,
            'description': insignia.description,
            'category': CriteriaType(category).label,
            'slug': style['slug'],
            'fallback_icon': style['icon'],
            'icon_url': _icon_url(insignia, number),
            'earned': earned_date is not None,
            'awarded_at': earned_date,
            'award_id': award_ids.get(insignia.pk),
        }

        by_type.setdefault(category, []).append(item)
        if item['earned']:
            earned_items.append(item)

    categories = []
    for value, label in CriteriaType.choices:
        items = by_type.get(value)
        if not items:
            continue

        style = CATEGORY_STYLES.get(value, DEFAULT_STYLE)
        categories.append({
            'label': label,
            'slug': style['slug'],
            'icon': style['icon'],
            'items': items,
            'earned_count': sum(1 for i in items if i['earned']),
            'total_count': len(items),
        })

    total_count = sum(c['total_count'] for c in categories)
    earned_count = len(earned_items)
    percent = round(earned_count * 100 / total_count) if total_count else 0

    recent = sorted(earned_items, key=lambda i: i['awarded_at'], reverse=True)[:recent_limit]

    return {
        'categories': categories,
        'earned_count': earned_count,
        'total_count': total_count,
        'percent': percent,
        'recent': recent,
    }
