"""Repairs demo recipes created by older seed versions without deleting data."""
from django.core.management.base import BaseCommand
from recipes.models import Ingredient, Recipe, RecipeIngredient
from recipes.services import NutritionCalculator
from .seed_recipes import PROFILES, RECIPES
from .seed_more_recipes import DATA, PROFILE_BY_CATEGORY

INITIAL_PROFILES = {"Piletina sa pirinčem": "chicken_rice", "Piletina sa krompirom": "chicken_pot", "Tuna salata": "tuna_toast", "Ovsena kaša": "oats_banana", "Omlet sa povrćem": "eggs"}

def profile_for(recipe):
    first_batch = {title: profile for _, title, profile in RECIPES}
    if recipe.title in first_batch: return first_batch[recipe.title]
    for category, titles in DATA.items():
        if recipe.title in titles: return PROFILE_BY_CATEGORY[category]
    return INITIAL_PROFILES.get(recipe.title, "veg_rice")

def instructions_for(recipe, profile, ingredients):
    names = ", ".join(item.ingredient.name.lower() for item in ingredients)
    steps = [f"Pripremite sastojke za {recipe.title.lower()} i iseckajte ih prema potrebi.", f"Zagrejte posudu na srednjoj vatri i prvo obradite {ingredients[0].ingredient.name.lower()}.", f"Dodajte preostale sastojke ({names}) redom, uz povremeno mešanje."]
    if profile in {"chicken_rice", "turkey_rice", "beef_rice", "veg_rice", "salmon_rice", "eggs_rice"}: steps.append("Dodajte malo vode po potrebi, poklopite i kuvajte dok pirinač ne omekša.")
    elif profile in {"chicken_pasta", "meat_pasta", "tuna_pasta", "veg_pasta"}: steps.append("Skuvajte testeninu al dente, sjedinite je sa sosom i kratko zagrejte.")
    elif profile in {"beans", "lentils", "peas_pot", "veg_pot", "beef_pot", "chicken_pot", "pork_potato"}: steps.append("Kuvajte poklopljeno na tihoj vatri dok povrće i glavni sastojak ne postanu mekani.")
    elif profile in {"salad", "tuna_toast", "toast"}: steps.append("Sjedinite sastojke neposredno pre serviranja kako bi obrok ostao svež.")
    else: steps.append("Proverite da li je glavni sastojak potpuno termički obrađen.")
    steps.append(f"Začinite po ukusu i poslužite {recipe.title.lower()} toplo ili sveže, zavisno od jela.")
    return "\n".join(steps)

class Command(BaseCommand):
    help = "Dopunjava sastojke, nutritivne vrednosti i jedinstvena uputstva za postojeće demo recepte."
    def handle(self, *args, **options):
        added_lines = updated = 0
        for recipe in Recipe.objects.prefetch_related("recipe_ingredients__ingredient"):
            profile = profile_for(recipe)
            if not recipe.recipe_ingredients.exists():
                for name, quantity, unit in PROFILES[profile]:
                    ingredient = Ingredient.objects.get(name=name)
                    _, made = RecipeIngredient.objects.get_or_create(recipe=recipe, ingredient=ingredient, defaults={"quantity": quantity, "unit": unit})
                    added_lines += int(made)
            lines = list(recipe.recipe_ingredients.select_related("ingredient"))
            recipe.instructions = instructions_for(recipe, profile, lines)
            recipe.description = f"{recipe.title} je pažljivo pripremljen recept sa sastojcima dostupnim u Srbiji."
            totals = NutritionCalculator.calculate(recipe)
            recipe.calories, recipe.protein = totals["calories"], totals["protein"]
            recipe.carbohydrates, recipe.fat, recipe.fiber = totals["carbs"], totals["fat"], totals["fiber"]
            recipe.save(update_fields=["instructions", "description", "calories", "protein", "carbohydrates", "fat", "fiber"])
            updated += 1
        self.stdout.write(self.style.SUCCESS(f"Popravljeno recepata: {updated}; dodato sastojaka: {added_lines}."))
