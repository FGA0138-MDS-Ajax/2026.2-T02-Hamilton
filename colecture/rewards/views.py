from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .selectors import get_insignia_overview


@login_required
def insignias_view(request):
    """Lista todas as insígnias do usuário, agrupadas por categoria."""
    overview = get_insignia_overview(request.user)
    return render(request, 'rewards/insignias.html', {'overview': overview})
