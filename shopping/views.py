from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from recipes.models import Recipe
from .models import ShoppingList, ShoppingListItem
@login_required
def shopping_list(request):
    cart, _ = ShoppingList.objects.get_or_create(user=request.user)
    return render(request, "shopping/list.html", {"cart": cart})
@login_required
def add_recipe(request, slug):
    recipe = get_object_or_404(Recipe, slug=slug); cart, _ = ShoppingList.objects.get_or_create(user=request.user)
    for line in recipe.recipe_ingredients.all():
        item, made = ShoppingListItem.objects.get_or_create(shopping_list=cart, ingredient=line.ingredient, unit=line.unit, defaults={"quantity": line.quantity})
        if not made: item.quantity += line.quantity; item.save()
    return redirect("shopping:list")
@login_required
def toggle_item(request, pk):
    item = get_object_or_404(ShoppingListItem, pk=pk, shopping_list__user=request.user); item.purchased = not item.purchased; item.save()
    return redirect("shopping:list")
