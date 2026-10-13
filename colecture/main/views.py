from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required

def index(request):
    if request.user.is_authenticated:
        return redirect('main:perfil')
    return render(request, 'main/index.html')

def perfil(request):
    if request.user.is_authenticated:
        return render(request, 'main/perfil.html')
    return render(request, 'main/index.html')
