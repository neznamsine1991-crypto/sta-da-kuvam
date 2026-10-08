from datetime import date
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from recipes.models import Category, Ingredient, Recipe, RecipeIngredient
from prices.models import Supermarket, IngredientPrice

class Command(BaseCommand):
    help = "Unosi jasno označene DEMO recepte i cene za razvoj."
    def handle(self, *args, **kwargs):
        categories = {n: Category.objects.get_or_create(name=n, defaults={"slug": slugify(n)})[0] for n in ["Doručak", "Ručak", "Večera", "Salate", "Deserti"]}
        raw = [("Pileći file", "Meso", 110, 23, 0, 2, 0), ("Pirinač", "Žitarice", 360, 7, 79, 1, 1), ("Krompir", "Povrće", 77, 2, 17, 0, 2), ("Jaje", "Mlečni proizvodi", 143, 13, 1, 10, 0), ("Paradajz", "Povrće", 18, 1, 4, 0, 1), ("Tunjevina", "Riba", 116, 26, 0, 1, 0), ("Ovsene pahuljice", "Žitarice", 389, 17, 66, 7, 10)]
        ingredients = {}
        for n, cat, kcal, pro, carb, fat, fiber in raw:
            ingredients[n] = Ingredient.objects.get_or_create(name=n, defaults={"slug":slugify(n), "category":cat, "calories_per_100g":kcal, "protein_per_100g":pro, "carbs_per_100g":carb, "fat_per_100g":fat, "fiber_per_100g":fiber})[0]
        markets = {n: Supermarket.objects.get_or_create(name=n, defaults={"slug":slugify(n)})[0] for n in ["Lidl", "Maxi", "Univerexport"]}
        base_prices = {"Pileći file":650, "Pirinač":180, "Krompir":100, "Jaje":25, "Paradajz":220, "Tunjevina":1100, "Ovsene pahuljice":220}
        for i, (name, price) in enumerate(base_prices.items()):
            for j, market in enumerate(markets.values()):
                IngredientPrice.objects.get_or_create(ingredient=ingredients[name], supermarket=market, valid_from=date.today(), defaults={"price":price+j*20, "quantity":1000, "unit":"g", "source":"DEMO / uzorak"})
        recipes = [("Piletina sa pirinčem", "Ručak", "Sočan, brz ručak pun proteina.", [("Pileći file",500),("Pirinač",250),("Paradajz",150)]), ("Piletina sa krompirom", "Ručak", "Klasičan porodični obrok.", [("Pileći file",500),("Krompir",700)]), ("Tuna salata", "Salate", "Lagana večera sa dosta proteina.", [("Tunjevina",160),("Paradajz",250)]), ("Ovsena kaša", "Doručak", "Doručak koji drži sitost.", [("Ovsene pahuljice",100)]), ("Omlet sa povrćem", "Doručak", "Jednostavan slani doručak.", [("Jaje",3),("Paradajz",150)])]
        for title, cat, desc, rows in recipes:
            recipe, made = Recipe.objects.get_or_create(title=title, defaults={"slug":slugify(title), "category":categories[cat], "description":desc, "instructions":"Pripremite sastojke.\nKuvajte ili pecite dok ne bude gotovo.\nPoslužite toplo.", "servings":2, "prep_time":10, "cook_time":20, "featured":True, "calories":500, "protein":30})
            if made:
                for name, quantity in rows: RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredients[name], quantity=quantity, unit="piece" if name == "Jaje" else "g")
        self.stdout.write(self.style.SUCCESS("DEMO podaci su spremni."))
