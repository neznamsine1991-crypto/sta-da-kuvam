from decimal import Decimal
class NutritionCalculator:
    @classmethod
    def calculate(cls, recipe):
        totals = {key: Decimal("0") for key in ("calories", "protein", "carbs", "fat", "fiber")}
        for item in recipe.recipe_ingredients.select_related("ingredient"):
            factor = item.quantity / Decimal("100") if item.unit in ("g", "ml") else item.quantity
            ing = item.ingredient
            totals["calories"] += ing.calories_per_100g * factor
            totals["protein"] += ing.protein_per_100g * factor
            totals["carbs"] += ing.carbs_per_100g * factor
            totals["fat"] += ing.fat_per_100g * factor
            totals["fiber"] += ing.fiber_per_100g * factor
        return {key: round(value / recipe.servings, 1) for key, value in totals.items()}
