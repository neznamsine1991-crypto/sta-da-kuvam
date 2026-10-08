"""Dodaje drugu grupu od 100 različitih recepata, bez dupliciranja."""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from recipes.models import Category, Recipe, RecipeIngredient
from recipes.services import NutritionCalculator
from .seed_recipes import INGREDIENTS, PROFILES

DATA = {
"Piletina": ["Pileće rolnice sa sirom", "Piletina sa susamom", "Piletina terijaki", "Pileći kari", "Pileći file u rerni", "Piletina sa limunom", "Pileći ražnjići", "Piletina sa spanaćem", "Piletina u paradajz sosu", "Piletina sa graškom"],
"Junetina": ["Juneće šnicle u sosu", "Juneći paprikaš", "Juneći rižoto", "Juneće meso sa povrćem", "Beef burger", "Juneća supa", "Juneći wok", "Junetina sa pečurkama", "Juneći gulaš sa krompirom", "Junetina u rerni"],
"Svinjetina": ["Svinjski paprikaš", "Svinjske šnicle", "Pečena svinjetina", "Svinjetina sa povrćem", "Svinjetina u sosu od pečuraka", "Krmenadle sa krompirom", "Podvarak", "Svinjetina sa kupusom", "Svinjski gulaš", "Svinjske rolnice"],
"Riba": ["Pastrmka iz rerne", "Losos sa povrćem", "Riba sa blitvom", "Riblji file sa povrćem", "Tuna rižoto", "Tuna punjene paprike", "Oslić u paradajz sosu", "Pastrmka sa krompirom", "Riblji burger", "Losos salata"],
"Vegetarijansko": ["Tikvice sa sirom", "Povrtna musaka", "Povrtni kuskus", "Boranija sa krompirom", "Pohovane tikvice", "Karfiol iz rerne", "Povrtne pljeskavice", "Paprikaš od pečuraka", "Krompir sa spanaćem", "Pita sa povrćem"],
"Visok protein": ["Ćuretina sa tikvicama", "Proteinska tortilja", "Grčki jogurt proteinska činija", "Jaja i sir fit tanjir", "Piletina meal prep", "Tuna rice bowl", "Junetina fit tanjir", "Piletina sa sočivom", "Proteinski sendvič", "Ćureće ćufte"],
"Domaća jela": ["Uštipci", "Kačamak sa kajmakom", "Grašak sa mesom", "Domaća supa sa knedlama", "Pita zeljanica", "Pohovana piletina", "Kiseli kupus sa mesom", "Svadbarski kupus", "Kuvani krompir sa sirom", "Gomboce sa šljivama"],
"Brzi obroci": ["Tost sa sirom i paradajzom", "Jaja na oko sa povrćem", "Brzi pileći wok", "Pasta sa sirom", "Tuna wrap", "Piletina u tortilji", "Prženi pirinač", "Brzi rižoto", "Sendvič sa jajima", "Pizza tost"],
"Salate": ["Cezar salata sa piletinom", "Salata od pasulja", "Salata sa kinoom", "Krompir salata", "Salata od cvekle", "Mediteranska salata", "Salata sa testeninom", "Salata od leblebija", "Pileća cezar salata", "Salata sa grilovanim povrćem"],
"Deserti": ["Ovseni kolač sa jabukom", "Banana hleb", "Koh", "Voćna salata", "Čokoladni griz", "Kolač od šargarepe", "Zdravi mafini", "Pita sa jabukama", "Keks torta", "Proteinski puding"],
}
PROFILE_BY_CATEGORY = {"Piletina":"chicken_veg", "Junetina":"beef_pot", "Svinjetina":"pork_potato", "Riba":"fish_potato", "Vegetarijansko":"veg_rice", "Visok protein":"chicken_rice", "Domaća jela":"meat_potato", "Brzi obroci":"eggs_rice", "Salate":"salad", "Deserti":"protein_pancakes"}

class Command(BaseCommand):
    help = "Idempotentno dodaje tačno 100 novih recepata uz postojeće podatke."
    def handle(self, *args, **kwargs):
        records = [(category, title) for category, titles in DATA.items() for title in titles]
        if len(records) != 100: raise RuntimeError("Skup recepata mora imati 100 stavki.")
        ingredients = {name: __import__("recipes.models", fromlist=["Ingredient"]).Ingredient.objects.get_or_create(name=name, defaults={"slug":slugify(name), "category":data[0], "calories_per_100g":data[1], "protein_per_100g":data[2], "carbs_per_100g":data[3], "fat_per_100g":data[4], "fiber_per_100g":data[5]})[0] for name, data in INGREDIENTS.items()}
        created = 0
        for category_name, title in records:
            category, _ = Category.objects.get_or_create(name=category_name, defaults={"slug":slugify(category_name)})
            recipe, made = Recipe.objects.get_or_create(slug=slugify(title), defaults={"title":title, "category":category, "description":f"{title} je ukusan recept od sastojaka dostupnih u lokalnim prodavnicama.", "instructions":"Pripremite i iseckajte sastojke.\nZagrejte posudu i dodajte glavne sastojke.\nKuvajte uz povremeno mešanje dok obrok ne bude gotov.\nPoslužite sveže i toplo.", "servings":4, "prep_time":10, "cook_time":25, "published":True})
            if made:
                created += 1
                for name, qty, unit in PROFILES[PROFILE_BY_CATEGORY[category_name]]: RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredients[name], quantity=qty, unit=unit)
                nutrition = NutritionCalculator.calculate(recipe)
                recipe.calories, recipe.protein, recipe.carbohydrates, recipe.fat, recipe.fiber = nutrition["calories"], nutrition["protein"], nutrition["carbs"], nutrition["fat"], nutrition["fiber"]
                recipe.save(update_fields=["calories", "protein", "carbohydrates", "fat", "fiber"])
        self.stdout.write(self.style.SUCCESS(f"Dodato {created} od 100 recepata. Ponovno pokretanje ne pravi duplikate."))
