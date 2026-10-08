from django.conf import settings
from django.db import models
from recipes.models import Ingredient
class ShoppingList(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shopping_lists")
    name = models.CharField(max_length=100, default="Moja lista")
    preferred_supermarket = models.ForeignKey("prices.Supermarket", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
class ShoppingListItem(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name="items")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=12, default="g")
    purchased = models.BooleanField(default=False)
    class Meta: unique_together = [("shopping_list", "ingredient", "unit")]
