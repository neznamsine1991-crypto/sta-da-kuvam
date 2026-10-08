"""Idempotentno puni bazu sa 100 dodatnih, jasno označenih DEMO recepata."""
from datetime import date
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from recipes.models import Category, Ingredient, Recipe, RecipeIngredient
from recipes.services import NutritionCalculator
from prices.models import IngredientPrice, Supermarket

INGREDIENTS = {
    "Piletina": ("Meso", 110, 23, 0, 2, 0, 650), "Ćuretina": ("Meso", 114, 24, 0, 2, 0, 820),
    "Junetina": ("Meso", 190, 26, 0, 9, 0, 1050), "Mleveno meso": ("Meso", 250, 20, 0, 18, 0, 850),
    "Svinjetina": ("Meso", 242, 27, 0, 14, 0, 780), "Oslić": ("Riba", 90, 18, 0, 1, 0, 720),
    "Losos": ("Riba", 208, 20, 0, 13, 0, 1850), "Tunjevina": ("Riba", 116, 26, 0, 1, 0, 1100),
    "Jaja": ("Jaja", 143, 13, 1, 10, 0, 25), "Sir": ("Mlečni proizvodi", 280, 20, 2, 21, 0, 800),
    "Grčki jogurt": ("Mlečni proizvodi", 73, 9, 4, 2, 0, 450), "Mleko": ("Mlečni proizvodi", 61, 3, 5, 3, 0, 140),
    "Pirinač": ("Žitarice", 360, 7, 79, 1, 1, 180), "Testenina": ("Žitarice", 350, 12, 72, 2, 3, 240),
    "Ovsene pahuljice": ("Žitarice", 389, 17, 66, 7, 10, 220), "Brašno": ("Žitarice", 364, 10, 76, 1, 3, 120),
    "Krompir": ("Povrće", 77, 2, 17, 0, 2, 100), "Luk": ("Povrće", 40, 1, 9, 0, 2, 100),
    "Paradajz": ("Povrće", 18, 1, 4, 0, 1, 220), "Paprika": ("Povrće", 31, 1, 6, 0, 2, 260),
    "Tikvica": ("Povrće", 17, 1, 3, 0, 1, 180), "Pečurke": ("Povrće", 22, 3, 3, 0, 1, 400),
    "Šargarepa": ("Povrće", 41, 1, 10, 0, 3, 120), "Spanać": ("Povrće", 23, 3, 4, 0, 2, 350),
    "Pasulj": ("Mahunarke", 333, 21, 60, 1, 15, 320), "Sočivo": ("Mahunarke", 353, 25, 60, 1, 11, 330),
    "Grašak": ("Mahunarke", 81, 5, 14, 0, 5, 260), "Kupus": ("Povrće", 25, 1, 6, 0, 3, 100),
    "Maslinovo ulje": ("Ulje", 884, 0, 0, 100, 0, 1300), "Banana": ("Voće", 89, 1, 23, 0, 3, 180),
    "Jabuka": ("Voće", 52, 0, 14, 0, 2, 120), "Hleb": ("Pekarski proizvodi", 265, 9, 49, 3, 3, 160),
    "Kukuruzno brašno": ("Žitarice", 365, 9, 76, 4, 7, 180), "Šećer": ("Ostalo", 387, 0, 100, 0, 0, 130),
}

RECIPES = [
 # 10 doručaka
 ("Doručak", "Omlet sa sirom", "eggs"), ("Doručak", "Jaja sa spanaćem", "spinach_eggs"), ("Doručak", "Jaja sa šunkom", "eggs"), ("Doručak", "Ovsena kaša sa bananom", "oats_banana"), ("Doručak", "Ovsena kaša sa jabukom", "oats_apple"), ("Doručak", "Proteinske palačinke", "protein_pancakes"), ("Doručak", "Jogurt sa voćem i ovsom", "yogurt"), ("Doručak", "Tost sa jajima", "toast"), ("Doručak", "Proja sa jogurtom", "proja"), ("Doručak", "Kačamak sa sirom", "polenta"),
 # 20 ručkova
 ("Ručak", "Pileći paprikaš", "chicken_pot"), ("Ručak", "Piletina u sosu od pečuraka", "chicken_mushroom"), ("Ručak", "Pileći rižoto", "chicken_rice"), ("Ručak", "Piletina sa testeninom", "chicken_pasta"), ("Ručak", "Gulaš od junetine", "beef_pot"), ("Ručak", "Ćufte u paradajz sosu", "meat_pasta"), ("Ručak", "Musaka sa mesom", "meat_potato"), ("Ručak", "Špagete bolonjeze", "meat_pasta"), ("Ručak", "Lazanje sa mesom", "meat_pasta"), ("Ručak", "Punjene paprike", "meat_potato"), ("Ručak", "Sarma", "meat_potato"), ("Ručak", "Svinjski file sa krompirom", "pork_potato"), ("Ručak", "Oslić sa krompirom", "fish_potato"), ("Ručak", "Losos sa pirinčem", "salmon_rice"), ("Ručak", "Đuveč sa piletinom", "chicken_rice"), ("Ručak", "Pileća supa sa rezancima", "chicken_pasta"), ("Ručak", "Pasta sa tunjevinom", "tuna_pasta"), ("Ručak", "Riblja čorba", "fish_potato"), ("Ručak", "Faširane šnicle", "meat_potato"), ("Ručak", "Pljeskavice sa krompirom", "meat_potato"),
 # 20 večera
 ("Večera", "Pečena piletina sa povrćem", "chicken_veg"), ("Večera", "Piletina sa medom i senfom", "chicken_veg"), ("Večera", "Grilovana piletina", "chicken_veg"), ("Večera", "Tuna sendvič", "tuna_toast"), ("Večera", "Pečeni oslić", "fish_potato"), ("Večera", "Pasta primavera", "veg_pasta"), ("Večera", "Povrtni rižoto", "veg_rice"), ("Večera", "Sataraš", "veg_pot"), ("Večera", "Prebranac", "beans"), ("Večera", "Pasulj sa povrćem", "beans"), ("Večera", "Krompir paprikaš", "veg_pot"), ("Večera", "Sočivo sa povrćem", "lentils"), ("Večera", "Pita sa sirom", "cheese_pie"), ("Večera", "Pita sa krompirom", "potato_pie"), ("Večera", "Gibanica", "cheese_pie"), ("Večera", "Pita sa mesom", "meat_pasta"), ("Večera", "Povrće iz rerne", "chicken_veg"), ("Večera", "Jaja u paradajz sosu", "eggs"), ("Večera", "Palenta sa sirom", "polenta"), ("Večera", "Pohovani oslić", "fish_potato"),
 # 10 brzi
 ("Brzi obroci", "Quesadilla sa piletinom", "chicken_pasta"), ("Brzi obroci", "Pileći wrap", "chicken_veg"), ("Brzi obroci", "Brza pasta sa paradajzom", "veg_pasta"), ("Brzi obroci", "Tost sa tunjevinom", "tuna_toast"), ("Brzi obroci", "Grčka salata", "salad"), ("Brzi obroci", "Šopska salata", "salad"), ("Brzi obroci", "Cezar salata", "chicken_veg"), ("Brzi obroci", "Pirinač sa jajima", "eggs_rice"), ("Brzi obroci", "Pasta sa pečurkama", "veg_pasta"), ("Brzi obroci", "Sendvič sa piletinom", "chicken_veg"),
 # 10 high protein
 ("Visok protein", "Pileći proteinski bowl", "chicken_rice"), ("Visok protein", "Ćureći rice bowl", "turkey_rice"), ("Visok protein", "Goveđi rice bowl", "beef_rice"), ("Visok protein", "Tuna proteinska pasta", "tuna_pasta"), ("Visok protein", "Omlet sa grčkim jogurtom", "spinach_eggs"), ("Visok protein", "Piletina sa brokolijem", "chicken_veg"), ("Visok protein", "Losos proteinski tanjir", "salmon_rice"), ("Visok protein", "Junetina sa povrćem", "beef_pot"), ("Visok protein", "Piletina i krompir fit", "chicken_pot"), ("Visok protein", "Proteinska ovsena kaša", "protein_pancakes"),
 # 10 budget
 ("Jeftino", "Pasulj na vodi", "beans"), ("Jeftino", "Grašak sa krompirom", "peas_pot"), ("Jeftino", "Pirinač sa povrćem", "veg_rice"), ("Jeftino", "Popara", "toast"), ("Jeftino", "Krompir čorba", "veg_pot"), ("Jeftino", "Pasta u paradajz sosu", "veg_pasta"), ("Jeftino", "Proja", "proja"), ("Jeftino", "Palenta sa jogurtom", "polenta"), ("Jeftino", "Jaja sa krompirom", "eggs_rice"), ("Jeftino", "Sočivo paprikaš", "lentils"),
 # 8 vegetarian
 ("Vegetarijansko", "Punjene paprike bez mesa", "veg_rice"), ("Vegetarijansko", "Tikvice sa pirinčem", "veg_rice"), ("Vegetarijansko", "Pasta sa tikvicama", "veg_pasta"), ("Vegetarijansko", "Povrtni wok", "chicken_veg"), ("Vegetarijansko", "Pečurke sa pirinčem", "veg_rice"), ("Vegetarijansko", "Musaka od krompira", "veg_pot"), ("Vegetarijansko", "Pita sa spanaćem", "spinach_eggs"), ("Vegetarijansko", "Povrtna lazanja", "veg_pasta"),
 # 5 soups stews
 ("Supe i čorbe", "Povrtna supa", "veg_pot"), ("Supe i čorbe", "Paradajz čorba", "veg_pot"), ("Supe i čorbe", "Čorbast pasulj", "beans"), ("Supe i čorbe", "Grašak čorba", "peas_pot"), ("Supe i čorbe", "Krem čorba od pečuraka", "chicken_mushroom"),
 # 4 salads
 ("Salate", "Pileća salata", "chicken_veg"), ("Salate", "Tuna salata sa jajima", "tuna_toast"), ("Salate", "Kupus salata", "salad"), ("Salate", "Paradajz i sir salata", "salad"),
 # 3 desserts
 ("Deserti", "Palačinke", "protein_pancakes"), ("Deserti", "Sutlijaš", "oats_banana"), ("Deserti", "Griz na mleku", "oats_apple"),
]

PROFILES = {
 "eggs": [("Jaja", 4, "piece"), ("Paradajz", 200, "g"), ("Sir", 80, "g")], "spinach_eggs": [("Jaja", 4, "piece"), ("Spanać", 200, "g"), ("Sir", 60, "g")],
 "oats_banana": [("Ovsene pahuljice", 160, "g"), ("Mleko", 500, "g"), ("Banana", 250, "g")], "oats_apple": [("Ovsene pahuljice", 160, "g"), ("Mleko", 500, "g"), ("Jabuka", 250, "g")], "protein_pancakes": [("Ovsene pahuljice", 150, "g"), ("Jaja", 3, "piece"), ("Grčki jogurt", 250, "g"), ("Banana", 150, "g")], "yogurt": [("Grčki jogurt", 500, "g"), ("Ovsene pahuljice", 120, "g"), ("Jabuka", 250, "g")], "toast": [("Hleb", 250, "g"), ("Jaja", 4, "piece"), ("Sir", 80, "g")], "proja": [("Kukuruzno brašno", 250, "g"), ("Jaja", 2, "piece"), ("Grčki jogurt", 300, "g")], "polenta": [("Kukuruzno brašno", 250, "g"), ("Sir", 150, "g"), ("Grčki jogurt", 250, "g")],
 "chicken_pot": [("Piletina", 600, "g"), ("Krompir", 700, "g"), ("Luk", 150, "g"), ("Paprika", 200, "g")], "chicken_mushroom": [("Piletina", 600, "g"), ("Pečurke", 400, "g"), ("Pirinač", 250, "g")], "chicken_rice": [("Piletina", 650, "g"), ("Pirinač", 300, "g"), ("Šargarepa", 200, "g")], "chicken_pasta": [("Piletina", 600, "g"), ("Testenina", 350, "g"), ("Paradajz", 300, "g")], "chicken_veg": [("Piletina", 600, "g"), ("Tikvica", 300, "g"), ("Paprika", 250, "g"), ("Paradajz", 250, "g")],
 "beef_pot": [("Junetina", 650, "g"), ("Krompir", 600, "g"), ("Luk", 180, "g"), ("Šargarepa", 200, "g")], "meat_pasta": [("Mleveno meso", 600, "g"), ("Testenina", 350, "g"), ("Paradajz", 400, "g"), ("Luk", 150, "g")], "meat_potato": [("Mleveno meso", 550, "g"), ("Krompir", 900, "g"), ("Luk", 150, "g"), ("Paprika", 250, "g")], "pork_potato": [("Svinjetina", 650, "g"), ("Krompir", 800, "g"), ("Luk", 150, "g")],
 "fish_potato": [("Oslić", 700, "g"), ("Krompir", 800, "g"), ("Šargarepa", 200, "g")], "salmon_rice": [("Losos", 600, "g"), ("Pirinač", 300, "g"), ("Spanać", 200, "g")], "tuna_pasta": [("Tunjevina", 350, "g"), ("Testenina", 350, "g"), ("Paradajz", 300, "g")], "tuna_toast": [("Tunjevina", 300, "g"), ("Hleb", 300, "g"), ("Paradajz", 250, "g")],
 "veg_pasta": [("Testenina", 350, "g"), ("Tikvica", 350, "g"), ("Pečurke", 250, "g"), ("Paradajz", 350, "g")], "veg_rice": [("Pirinač", 350, "g"), ("Paprika", 250, "g"), ("Tikvica", 300, "g"), ("Šargarepa", 200, "g")], "veg_pot": [("Krompir", 900, "g"), ("Paprika", 300, "g"), ("Paradajz", 350, "g"), ("Luk", 180, "g")], "beans": [("Pasulj", 450, "g"), ("Luk", 200, "g"), ("Paprika", 200, "g")], "lentils": [("Sočivo", 450, "g"), ("Šargarepa", 250, "g"), ("Luk", 180, "g")], "peas_pot": [("Grašak", 600, "g"), ("Krompir", 700, "g"), ("Šargarepa", 200, "g")], "eggs_rice": [("Jaja", 5, "piece"), ("Krompir", 700, "g"), ("Luk", 150, "g")], "salad": [("Paradajz", 400, "g"), ("Paprika", 250, "g"), ("Sir", 180, "g")], "turkey_rice": [("Ćuretina", 650, "g"), ("Pirinač", 300, "g"), ("Paprika", 250, "g")], "beef_rice": [("Junetina", 650, "g"), ("Pirinač", 300, "g"), ("Šargarepa", 200, "g")], "cheese_pie": [("Brašno", 350, "g"), ("Sir", 300, "g"), ("Jaja", 3, "piece")], "potato_pie": [("Brašno", 350, "g"), ("Krompir", 700, "g"), ("Luk", 150, "g")],
}

class Command(BaseCommand):
    help = "Dodaje tačno 100 novih DEMO recepata; bez menjanja postojećih."
    def handle(self, *args, **kwargs):
        if len(RECIPES) != 100:
            raise RuntimeError(f"Skup mora imati 100 recepata, ima {len(RECIPES)}")
        categories = {name: Category.objects.get_or_create(name=name, defaults={"slug": slugify(name)})[0] for name, _, _ in RECIPES}
        markets = [Supermarket.objects.get_or_create(name=n, defaults={"slug":slugify(n)})[0] for n in ("Lidl", "Maxi", "Univerexport")]
        ingredients = {}
        for name, (group, kcal, protein, carbs, fat, fiber, price) in INGREDIENTS.items():
            ingredient, _ = Ingredient.objects.get_or_create(name=name, defaults={"slug":slugify(name), "category":group, "calories_per_100g":kcal, "protein_per_100g":protein, "carbs_per_100g":carbs, "fat_per_100g":fat, "fiber_per_100g":fiber})
            ingredients[name] = ingredient
            for i, market in enumerate(markets):
                IngredientPrice.objects.get_or_create(ingredient=ingredient, supermarket=market, valid_from=date.today(), defaults={"price":Decimal(price + i * 15), "quantity":1000, "unit":"g", "source":"DEMO / uzorak"})
        added = 0
        for category_name, title, profile in RECIPES:
            slug = slugify(title)
            recipe, created = Recipe.objects.get_or_create(slug=slug, defaults={"title":title, "category":categories[category_name], "description":f"{title} je praktičan domaći obrok sa sastojcima dostupnim u Srbiji.", "instructions":"Pripremite i iseckajte sve sastojke.\nZagrejte posudu i dodajte glavne sastojke redom.\nKuvajte uz povremeno mešanje dok sve ne omekša.\nZačinite po ukusu i poslužite toplo.", "servings":4, "prep_time":10 if category_name in ("Doručak", "Brzi obroci") else 15, "cook_time":15 if category_name == "Brzi obroci" else 30, "featured":False, "published":True})
            if created:
                added += 1
                for name, quantity, unit in PROFILES[profile]: RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredients[name], quantity=quantity, unit=unit)
                totals = NutritionCalculator.calculate(recipe)
                recipe.calories, recipe.protein, recipe.carbohydrates, recipe.fat, recipe.fiber = totals["calories"], totals["protein"], totals["carbs"], totals["fat"], totals["fiber"]
                recipe.save(update_fields=["calories", "protein", "carbohydrates", "fat", "fiber"])
        self.stdout.write(self.style.SUCCESS(f"Dodato: {added}; ukupan definisani skup: 100. Ponovno pokretanje ne pravi duplikate."))
