from django.shortcuts import render, redirect
from .forms import BookForm


# Create your views here.
def register_book(request):
    if request.method == "POST":
        form = BookForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("books:register_book")

    else:
        form = BookForm()

    return render(request, "books/book_form.html", {"form": form})
