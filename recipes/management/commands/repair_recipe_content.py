"""Improve the quality of the locally seeded demonstration recipes.

The project deliberately keeps its data local. This command is safe to run more
than once: it fills an empty ingredient list and rewrites only the generated
description, preparation steps and timing metadata.
"""
from hashlib import sha256

from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient, Recipe, RecipeIngredient
from recipes.services import NutritionCalculator
from .seed_recipes import PROFILES, RECIPES
from .seed_more_recipes import DATA, PROFILE_BY_CATEGORY


INITIAL_PROFILES = {
    "Piletina sa pirinčem": "chicken_rice",
    "Piletina sa krompirom": "chicken_pot",
    "Tuna salata": "tuna_toast",
    "Ovsena kaša": "oats_banana",
    "Omlet sa povrćem": "eggs",
}
FIRST_BATCH_PROFILES = {title: profile for _, title, profile in RECIPES}
MORE_BATCH_PROFILES = {
    title: PROFILE_BY_CATEGORY[category]
    for category, titles in DATA.items()
    for title in titles
}


def profile_for(recipe):
    return FIRST_BATCH_PROFILES.get(
        recipe.title,
        MORE_BATCH_PROFILES.get(recipe.title, INITIAL_PROFILES.get(recipe.title, "veg_rice")),
    )


def normalised_title(recipe):
    return recipe.title.casefold()


def pick(recipe, choices, offset=0):
    """Choose repeatable wording variation for this exact recipe title."""
    digest = sha256(f"{recipe.slug}:{offset}".encode()).digest()
    return choices[digest[0] % len(choices)]


def ingredient_names(ingredients):
    return [line.ingredient.name.lower() for line in ingredients]


def has(title, *needles):
    return any(needle in title for needle in needles)


def style_for(recipe, profile):
    title = normalised_title(recipe)
    if has(title, "salata", "činija", "tanjir"):
        return "cold"
    if has(title, "palač", "ustip", "uštip", "pohovan"):
        return "pan"
    if has(title, "pita", "gibanica", "lazanj", "musaka", "kolač", "mafin", "koh", "hleb", "torta", "gomboce", "proja"):
        return "bake"
    if has(title, "supa", "čorba", "gulaš", "paprikaš", "pasulj", "sočivo", "sarma", "podvarak", "svadbarski", "boranija", "grašak"):
        return "simmer"
    if has(title, "testen", "pasta", "špaget") or profile in {"chicken_pasta", "meat_pasta", "tuna_pasta", "veg_pasta"}:
        return "pasta"
    if has(title, "pirinač", "rižoto", "rice", "đuveč", "punjene paprike") or profile in {"chicken_rice", "turkey_rice", "beef_rice", "veg_rice", "salmon_rice"}:
        return "rice"
    if has(title, "sendvič", "tost", "wrap", "tortilj", "quesadilla", "burger", "pizza tost"):
        return "sandwich"
    if has(title, "kaša", "griz", "sutlijaš", "kačamak", "palenta", "puding"):
        return "porridge"
    if has(title, "rerna", "pečen", "ražnjić", "gril", "file", "šnicle", "krmenadle", "rolnice"):
        return "roast"
    return "skillet"


def timing_for(recipe, style):
    """Return intentionally varied, plausible times for simple and complex dishes."""
    title = normalised_title(recipe)
    complex_dishes = ("lazanja", "sarma", "gulaš", "svadbarski", "pasulj", "musaka", "punjene", "torta", "gomboce", "podvarak")
    quick_dishes = ("salata", "sendvič", "tost", "wrap", "činija", "jaja na oko", "omlet", "puding")
    if has(title, *quick_dishes):
        return 8, 12 if style != "cold" else 0
    if has(title, *complex_dishes):
        return 25, 60
    if style in {"bake", "simmer", "roast"}:
        return 20, 40
    if style in {"pasta", "rice"}:
        return 15, 25
    return 12, 20


def instructions_for(recipe, profile, ingredients):
    """Create an individual, title-aware preparation that matches the dish type."""
    names = ingredient_names(ingredients)
    if not names:
        raise CommandError(f"Recept nema sastojke: {recipe.title}")
    first = names[0]
    rest = ", ".join(names[1:]) or first
    style = style_for(recipe, profile)
    prep = pick(recipe, [
        f"Operite i pripremite sastojke za {recipe.title.lower()}; sve što se seče pripremite pre početka kuvanja.",
        f"Za {recipe.title.lower()} pripremite radnu površinu i odmerite {', '.join(names)}.",
        f"Prvo pripremite {', '.join(names)} kako bi {recipe.title.lower()} tekao bez prekida.",
    ])

    if style == "cold":
        steps = [
            prep,
            f"Isecite {', '.join(names)} na zalogaje približno iste veličine.",
            f"U većoj činiji pažljivo sjedinite {first} sa ostalim sastojcima: {rest}.",
            f"Začinite po ukusu i ostavite {recipe.title.lower()} 5 minuta da se ukusi povežu.",
            f"Poslužite {recipe.title.lower()} odmah, dok je svež i hrskav.",
        ]
    elif style == "pasta":
        steps = [
            prep,
            "Stavite vodu da provri i skuvajte testeninu al dente; sačuvajte malo vode od kuvanja.",
            f"Na umerenoj vatri pripremite {first}, zatim dodajte {rest} i dinstajte dok ne omekšaju.",
            "Dodajte oceđenu testeninu i malo sačuvane vode, pa sve mešajte dok se ne poveže.",
            f"Probajte, začinite po ukusu i poslužite {recipe.title.lower()} bez odlaganja.",
        ]
    elif style == "rice":
        steps = [
            prep,
            f"Na umerenoj vatri kratko obradite {first}, a zatim dodajte {rest}.",
            "Umešajte pirinač kada je prisutan, nalijte vodom po potrebi i poklopite.",
            "Kuvajte na tihoj vatri dok pirinač ne omekša i tečnost se gotovo ne upije; povremeno nežno promešajte.",
            f"Sklonite sa vatre, ostavite poklopljeno 5 minuta i poslužite {recipe.title.lower()}.",
        ]
    elif style == "simmer":
        steps = [
            prep,
            f"U šerpi na srednjoj vatri započnite sa {first}, pa dodajte {rest} i kratko prodinstajte.",
            "Nalijte toplom vodom toliko da sastojci budu pokriveni i kuvajte poklopljeno na laganoj vatri.",
            "Povremeno proverite gustinu; po potrebi dodajte malo vode i kuvajte dok glavni sastojak ne bude potpuno mekan.",
            f"Začinite pred kraj, ostavite {recipe.title.lower()} nekoliko minuta da odmori, pa poslužite toplo.",
        ]
    elif style == "bake":
        steps = [
            prep,
            "Zagrejte rernu na 180°C i pripremite blago podmazanu posudu za pečenje.",
            f"Sjedinite {first} sa sastojcima {rest}, rasporedite u posudu i poravnajte površinu.",
            "Pecite dok površina ne dobije boju, a sredina ne bude čvrsta; proverite čačkalicom kada je prikladno.",
            f"Ostavite {recipe.title.lower()} 10 minuta pre sečenja ili serviranja kako bi se lepo stegao.",
        ]
    elif style == "pan":
        steps = [
            prep,
            f"Zagrejte tiganj na srednjoj vatri i pripremite {first} u manjim turama ako je potrebno.",
            f"Dodajte {rest} redom, okrećući ili mešajući da se sve ravnomerno ispeče.",
            "Smanjite vatru ako jelo prebrzo tamni i nastavite dok sredina ne bude potpuno gotova.",
            f"Poslužite {recipe.title.lower()} odmah, uz dodatak po ukusu.",
        ]
    elif style == "sandwich":
        steps = [
            prep,
            f"Kratko zagrejte ili ispecite {first} ako je potrebno, a zatim pripremite {rest}.",
            "Složite sastojke ravnomerno da svaki zalogaj ima i glavni sastojak i prilog.",
            "Zatvorite, prepolovite i po želji kratko zapecite dok spolja ne postane hrskavo.",
            f"Poslužite {recipe.title.lower()} odmah dok je topao i svež.",
        ]
    elif style == "porridge":
        steps = [
            prep,
            f"U šerpici zagrejte tečne sastojke, pa postepeno umešajte {first} i ostatak: {rest}.",
            "Kuvajte na tihoj vatri uz neprekidno mešanje dok smesa ne postane kremasta i bez grudvica.",
            "Sklonite sa vatre kada postigne željenu gustinu; stajanjem će se dodatno zgusnuti.",
            f"Poslužite {recipe.title.lower()} toplo ili mlako, prema ukusu.",
        ]
    elif style == "roast":
        steps = [
            prep,
            f"Začinite {first} po ukusu i rasporedite ga sa sastojcima {rest} u jednom sloju.",
            "Pecite na 200°C, okrećući ili promešavajući na polovini pečenja da se sve ravnomerno ispeče.",
            "Proverite da li je glavni sastojak potpuno termički obrađen, a povrće mekano i blago karamelizovano.",
            f"Ostavite {recipe.title.lower()} 3 minuta da odmori, pa servirajte.",
        ]
    else:
        steps = [
            prep,
            f"Zagrejte tiganj na srednjoj vatri i prvo pripremite {first}.",
            f"Dodajte {rest} postepeno i mešajte dok sastojci ne omekšaju i ne puste ukus.",
            "Podesite jačinu vatre da ništa ne zagori i kuvajte dok glavni sastojak ne bude gotov.",
            f"Začinite po ukusu i poslužite {recipe.title.lower()} toplo.",
        ]

    # Recipes that genuinely take longer also receive an extra resting/checking
    # step, instead of pretending that they are as simple as a quick toast.
    if has(normalised_title(recipe), "lazanj", "sarma", "gulaš", "svadbarski", "pasulj", "musaka", "punjene", "torta", "gomboce", "podvarak"):
        steps.insert(-1, "Pre serviranja proverite da li su svi slojevi ili komadići jednako mekani i da li su se ukusi povezali.")

    if recipe.title.lower() not in "\n".join(steps).lower():
        raise CommandError(f"Priprema nema naziv recepta: {recipe.title}")
    return "\n".join(steps)


class Command(BaseCommand):
    help = "Dopunjava sastojke i piše zasebne, smislenije pripreme za svaki DEMO recept."

    def handle(self, *args, **options):
        added_lines = updated = 0
        for recipe in Recipe.objects.prefetch_related("recipe_ingredients__ingredient"):
            profile = profile_for(recipe)
            if not recipe.recipe_ingredients.exists():
                for name, quantity, unit in PROFILES[profile]:
                    ingredient = Ingredient.objects.get(name=name)
                    _, made = RecipeIngredient.objects.get_or_create(
                        recipe=recipe,
                        ingredient=ingredient,
                        defaults={"quantity": quantity, "unit": unit},
                    )
                    added_lines += int(made)
            lines = list(recipe.recipe_ingredients.select_related("ingredient"))
            recipe.instructions = instructions_for(recipe, profile, lines)
            recipe.description = (
                f"{recipe.title} je domaći recept sa sastojcima dostupnim u Srbiji, "
                f"prilagođen za {recipe.servings} porcije."
            )
            recipe.prep_time, recipe.cook_time = timing_for(recipe, style_for(recipe, profile))
            totals = NutritionCalculator.calculate(recipe)
            recipe.calories, recipe.protein = totals["calories"], totals["protein"]
            recipe.carbohydrates, recipe.fat, recipe.fiber = totals["carbs"], totals["fat"], totals["fiber"]
            recipe.save(update_fields=[
                "instructions", "description", "prep_time", "cook_time", "calories", "protein",
                "carbohydrates", "fat", "fiber",
            ])
            updated += 1
        self.stdout.write(self.style.SUCCESS(
            f"Updated recipes: {updated}; added ingredient lines: {added_lines}."
        ))
