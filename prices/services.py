from collections import defaultdict
from decimal import Decimal
from django.utils import timezone
from .models import IngredientPrice, Supermarket
class RecipeCostCalculator:
    def __init__(self, recipe): self.recipe = recipe
    def calculate(self):
        items = list(self.recipe.recipe_ingredients.select_related("ingredient"))
        totals = {}; details = {}
        for market in Supermarket.objects.filter(active=True):
            total = Decimal("0"); lines = []
            for item in items:
                price = IngredientPrice.objects.filter(ingredient=item.ingredient, supermarket=market, valid_from__lte=timezone.localdate()).order_by("-valid_from").first()
                if not price or price.unit != item.unit: continue
                cost = price.price_per_unit * item.quantity
                total += cost; lines.append((item, cost))
            if lines: totals[market] = total; details[market] = lines
        cheapest = min(totals, key=totals.get) if totals else None
        return {"totals": totals, "details": details, "cheapest": cheapest, "total": totals.get(cheapest, Decimal("0")), "per_serving": totals.get(cheapest, Decimal("0")) / self.recipe.servings}
