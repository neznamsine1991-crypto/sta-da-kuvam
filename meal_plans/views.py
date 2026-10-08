from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from recipes.models import Recipe
@login_required
def planner(request):
    recipes = Recipe.objects.filter(published=True)[:12]
    return render(request, "meal_plans/planner.html", {"recipes": recipes, "days": range(1, 8)})
