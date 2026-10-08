from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from .models import Category, Recipe
from .services import NutritionCalculator
from prices.services import RecipeCostCalculator
def home(request):
    recipes = Recipe.objects.filter(published=True).select_related("category").prefetch_related("recipe_ingredients__ingredient")
    return render(request, "home.html", {"featured": recipes.filter(featured=True)[:6], "recent": recipes.order_by("-id")[:12], "recipe_count": recipes.count(), "budget": recipes[:4], "categories": Category.objects.all()[:12]})
def recipe_list(request):
    qs = Recipe.objects.filter(published=True).select_related("category").prefetch_related("recipe_ingredients__ingredient")
    q = request.GET.get("q", "").strip()
    if q: qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(recipe_ingredients__ingredient__name__icontains=q)).distinct()
    if request.GET.get("category"): qs = qs.filter(category__slug=request.GET["category"])
    if request.GET.get("max_time"): qs = qs.filter(prep_time__lte=request.GET["max_time"])
    if request.GET.get("min_protein"): qs = qs.filter(protein__gte=request.GET["min_protein"])
    sort = request.GET.get("sort", "newest")
    ordering = {"newest":"-id", "name":"title", "calories":"calories", "protein":"-protein", "time":"prep_time"}
    qs = qs.order_by(ordering.get(sort, "-id"))
    return render(request, "recipes/list.html", {"recipes": qs, "categories": Category.objects.all(), "q": q, "sort": sort})
def category_list(request):
    return render(request, "recipes/categories.html", {"categories": Category.objects.all().order_by("name")})
def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    recipes = category.recipes.filter(published=True).prefetch_related("recipe_ingredients__ingredient")
    return render(request, "recipes/category_detail.html", {"category": category, "recipes": recipes})
def recipe_detail(request, slug):
    recipe = get_object_or_404(Recipe.objects.prefetch_related("recipe_ingredients__ingredient"), slug=slug, published=True)
    return render(request, "recipes/detail.html", {"recipe": recipe, "cost": RecipeCostCalculator(recipe).calculate(), "nutrition": NutritionCalculator.calculate(recipe)})
def suggestions(request):
    q = request.GET.get("q", "")
    return JsonResponse({"results": list(Recipe.objects.filter(published=True, title__icontains=q).values("title", "slug")[:6])})
@login_required
def toggle_favorite(request, slug):
    recipe = get_object_or_404(Recipe, slug=slug); favorites = request.user.profile.favorites
    favorites.remove(recipe) if recipe in favorites.all() else favorites.add(recipe)
    return redirect(recipe.get_absolute_url())
