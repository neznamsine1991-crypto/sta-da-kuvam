from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .forms import RegisterForm
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Nalog je uspešno napravljen. Dobro došli!")
            return redirect("users:dashboard")
    else: form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})
@login_required
def dashboard(request):
    return render(request, "users/dashboard.html", {"favorites": request.user.profile.favorites.all()[:6], "shopping": request.user.shopping_lists.first()})
