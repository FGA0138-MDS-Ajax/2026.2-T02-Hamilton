from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required

def index(request):
    if request.user.is_authenticated:
        return redirect('main:perfil')
    return render(request, 'main/index.html')

@login_required
def perfil(request):
    return render(request, 'main/perfil.html')