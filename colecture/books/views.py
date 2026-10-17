from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required;
from .forms import BookForm


# Create your views here.
@login_required
def register_book(request):
    if request.method == "POST":
        form = BookForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("books:register_book")

    else:
        form = BookForm()

    return render(request, "books/book_form.html", {"form": form})
