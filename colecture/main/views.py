from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required

def index(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    return render(request, 'main/index.html')

def search(request):
    return render(request, 'main/search.html')
