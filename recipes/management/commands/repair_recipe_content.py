"""Improve the quality of the locally seeded demonstration recipes.

The project deliberately keeps its data local. This command is safe to run more
than once: it fills an empty ingredient list and rewrites only the generated
description, preparation steps and timing metadata.
"""
from hashlib import sha256

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

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

# These dishes cannot be represented faithfully by a broad category profile.
# Their ingredients are deliberately listed here so they remain recognisable
# recipes instead of, for example, a "sarma" that looks like a potato stew.
PROFILE_OVERRIDES = {
    "Proteinski puding": [("Grčki jogurt", 500, "g"), ("Mleko", 350, "g"), ("Ovsene pahuljice", 100, "g"), ("Banana", 250, "g")],
    "Keks torta": [("Grčki jogurt", 500, "g"), ("Mleko", 350, "g"), ("Ovsene pahuljice", 160, "g"), ("Banana", 250, "g")],
    "Pita sa jabukama": [("Brašno", 400, "g"), ("Jabuka", 700, "g"), ("Šećer", 100, "g")],
    "Banana hleb": [("Brašno", 350, "g"), ("Banana", 400, "g"), ("Jaja", 3, "piece"), ("Šećer", 100, "g")],
    "Kolač od šargarepe": [("Brašno", 350, "g"), ("Šargarepa", 350, "g"), ("Jaja", 3, "piece"), ("Šećer", 120, "g")],
    "Zdravi mafini": [("Ovsene pahuljice", 220, "g"), ("Banana", 300, "g"), ("Jaja", 3, "piece"), ("Grčki jogurt", 200, "g")],
    "Koh": [("Jaja", 5, "piece"), ("Mleko", 700, "g"), ("Brašno", 180, "g"), ("Šećer", 140, "g")],
    "Čokoladni griz": [("Mleko", 700, "g"), ("Brašno", 100, "g"), ("Šećer", 80, "g")],
    "Cezar salata": [("Piletina", 450, "g"), ("Zelena salata", 250, "g"), ("Paradajz", 250, "g"), ("Sir", 120, "g")],
    "Cezar salata sa piletinom": [("Piletina", 450, "g"), ("Zelena salata", 250, "g"), ("Paradajz", 250, "g"), ("Sir", 120, "g")],
    "Pileća cezar salata": [("Piletina", 450, "g"), ("Zelena salata", 250, "g"), ("Paradajz", 250, "g"), ("Sir", 120, "g")],
    "Sarma": [("Mleveno meso", 550, "g"), ("Pirinač", 200, "g"), ("Kupus", 800, "g"), ("Luk", 150, "g")],
    "Punjene paprike": [("Mleveno meso", 550, "g"), ("Pirinač", 200, "g"), ("Paprika", 700, "g"), ("Luk", 150, "g")],
    "Punjene paprike bez mesa": [("Pirinač", 300, "g"), ("Paprika", 700, "g"), ("Tikvica", 300, "g"), ("Luk", 150, "g")],
    "Lazanje sa mesom": [("Mleveno meso", 600, "g"), ("Testenina", 400, "g"), ("Paradajz", 400, "g"), ("Sir", 250, "g"), ("Luk", 150, "g")],
    "Povrtna lazanja": [("Testenina", 400, "g"), ("Tikvica", 350, "g"), ("Pečurke", 300, "g"), ("Sir", 250, "g"), ("Paradajz", 300, "g")],
    "Musaka sa mesom": [("Mleveno meso", 550, "g"), ("Krompir", 900, "g"), ("Jaja", 3, "piece"), ("Sir", 180, "g"), ("Luk", 150, "g")],
    "Musaka od krompira": [("Krompir", 1000, "g"), ("Jaja", 3, "piece"), ("Sir", 220, "g"), ("Luk", 120, "g")],
    "Povrtna musaka": [("Krompir", 800, "g"), ("Tikvica", 400, "g"), ("Jaja", 3, "piece"), ("Sir", 220, "g"), ("Paradajz", 250, "g")],
    "Pita sa mesom": [("Brašno", 400, "g"), ("Mleveno meso", 500, "g"), ("Luk", 180, "g"), ("Jaja", 2, "piece")],
    "Pita sa krompirom": [("Brašno", 400, "g"), ("Krompir", 800, "g"), ("Luk", 180, "g")],
    "Pita sa sirom": [("Brašno", 400, "g"), ("Sir", 350, "g"), ("Jaja", 3, "piece"), ("Grčki jogurt", 250, "g")],
    "Pita sa spanaćem": [("Brašno", 400, "g"), ("Spanać", 400, "g"), ("Sir", 250, "g"), ("Jaja", 3, "piece")],
    "Pita zeljanica": [("Brašno", 400, "g"), ("Spanać", 400, "g"), ("Sir", 250, "g"), ("Jaja", 3, "piece")],
    "Pita sa povrćem": [("Brašno", 400, "g"), ("Tikvica", 350, "g"), ("Paprika", 250, "g"), ("Sir", 200, "g")],
    "Gibanica": [("Brašno", 400, "g"), ("Sir", 400, "g"), ("Jaja", 4, "piece"), ("Grčki jogurt", 300, "g")],
    "Prebranac": [("Pasulj", 500, "g"), ("Luk", 350, "g"), ("Paprika", 200, "g")],
    "Podvarak": [("Svinjetina", 650, "g"), ("Kupus", 900, "g"), ("Luk", 180, "g")],
    "Kiseli kupus sa mesom": [("Svinjetina", 650, "g"), ("Kupus", 900, "g"), ("Luk", 180, "g")],
    "Svadbarski kupus": [("Svinjetina", 650, "g"), ("Kupus", 1000, "g"), ("Luk", 180, "g")],
    "Riblji burger": [("Oslić", 600, "g"), ("Hleb", 300, "g"), ("Krompir", 400, "g"), ("Luk", 120, "g")],
}

EXTRA_INGREDIENTS = {
    "Zelena salata": ("Povrće", 15, 1, 3, 0, 1),
    "Tortilja": ("Pekarski proizvodi", 310, 8, 52, 8, 4),
    "Brokoli": ("Povrće", 34, 3, 7, 0, 3), "Susam": ("Ostalo", 573, 18, 23, 50, 12),
    "Limun": ("Voće", 29, 1, 9, 0, 3), "Med": ("Ostalo", 304, 0, 82, 0, 0),
    "Senf": ("Ostalo", 66, 4, 6, 4, 4), "Soja sos": ("Ostalo", 53, 8, 5, 1, 1),
    "Pastrmka": ("Riba", 148, 20, 0, 6, 0), "Blitva": ("Povrće", 19, 2, 4, 0, 2),
    "Karfiol": ("Povrće", 25, 2, 5, 0, 2), "Boranija": ("Povrće", 31, 2, 7, 0, 3),
    "Kuskus": ("Žitarice", 376, 13, 77, 1, 5), "Cvekla": ("Povrće", 43, 2, 10, 0, 3),
    "Leblebije": ("Mahunarke", 364, 19, 61, 6, 17), "Kinoa": ("Žitarice", 368, 14, 64, 6, 7),
    "Šunka": ("Meso", 145, 21, 1, 6, 0), "Kajmak": ("Mlečni proizvodi", 700, 3, 3, 75, 0),
    "Keks": ("Ostalo", 450, 6, 70, 16, 2), "Griz": ("Žitarice", 360, 12, 73, 1, 4),
    "Kakao": ("Ostalo", 228, 20, 58, 14, 33), "Šljiva": ("Voće", 46, 1, 11, 0, 1),
    "So": ("Začini", 0, 0, 0, 0, 0), "Biber": ("Začini", 251, 10, 64, 3, 25),
    "Beli luk": ("Povrće", 149, 6, 33, 1, 2), "Aleva paprika": ("Začini", 282, 14, 54, 13, 35),
    "Lovorov list": ("Začini", 313, 8, 75, 8, 26), "Prašak za pecivo": ("Ostalo", 53, 0, 28, 0, 0),
    "Vanila": ("Začini", 288, 0, 13, 0, 0), "Majonez": ("Ostalo", 680, 1, 1, 75, 0),
    "Slanina": ("Meso", 541, 37, 1, 42, 0), "Maslinovo ulje": ("Ulje", 884, 0, 0, 100, 0),
    "Cimet": ("Začini", 247, 4, 81, 1, 53),
    "Voda": ("Ostalo", 0, 0, 0, 0, 0), "Pavlaka": ("Mlečni proizvodi", 193, 3, 4, 19, 0),
    "Sirće": ("Ostalo", 18, 0, 1, 0, 0), "Origano": ("Začini", 265, 9, 69, 4, 43),
    "Peršun": ("Začini", 36, 3, 6, 1, 3), "Parmezan": ("Mlečni proizvodi", 431, 38, 4, 29, 0),
    "Suvi začin": ("Začini", 150, 5, 25, 3, 5), "Čokolada": ("Ostalo", 546, 5, 61, 31, 7),
    "Prezle": ("Pekarski proizvodi", 395, 13, 72, 5, 5),
    "Kari": ("Začini", 325, 14, 56, 14, 53),
}

# Exact ingredient lists for titles which a category profile cannot describe.
# Amounts are for four portions and intentionally remain simple, home-cooking data.
TITLE_INGREDIENTS = {
    "Sarma": [("Mleveno meso", 600, "g"), ("Kupus", 1200, "g"), ("Pirinač", 180, "g"), ("Luk", 250, "g"), ("Šargarepa", 150, "g"), ("Slanina", 150, "g"), ("Jaja", 1, "piece"), ("Beli luk", 15, "g"), ("Maslinovo ulje", 40, "g"), ("Aleva paprika", 10, "g"), ("Lovorov list", 2, "piece"), ("Brašno", 20, "g"), ("So", 8, "g"), ("Biber", 4, "g"), ("Voda", 1500, "ml")],
    "Musaka sa mesom": [("Krompir", 1000, "g"), ("Mleveno meso", 500, "g"), ("Luk", 180, "g"), ("Beli luk", 12, "g"), ("Šargarepa", 150, "g"), ("Mleko", 300, "ml"), ("Jaja", 3, "piece"), ("Maslinovo ulje", 35, "g"), ("So", 8, "g"), ("Biber", 4, "g")],
    "Cezar salata": [("Piletina", 500, "g"), ("Zelena salata", 350, "g"), ("Hleb", 180, "g"), ("Slanina", 120, "g"), ("Parmezan", 80, "g"), ("Jaja", 3, "piece"), ("Beli luk", 12, "g"), ("Majonez", 120, "g"), ("Pavlaka", 150, "g"), ("Senf", 15, "g"), ("Limun", 80, "g"), ("Maslinovo ulje", 40, "g"), ("So", 5, "g"), ("Biber", 3, "g")],
    "Cezar salata sa piletinom": [("Piletina", 500, "g"), ("Zelena salata", 350, "g"), ("Hleb", 180, "g"), ("Slanina", 120, "g"), ("Parmezan", 80, "g"), ("Jaja", 3, "piece"), ("Beli luk", 12, "g"), ("Majonez", 120, "g"), ("Pavlaka", 150, "g"), ("Senf", 15, "g"), ("Limun", 80, "g"), ("Maslinovo ulje", 40, "g"), ("So", 5, "g"), ("Biber", 3, "g")],
    "Pileća cezar salata": [("Piletina", 500, "g"), ("Zelena salata", 350, "g"), ("Hleb", 180, "g"), ("Slanina", 120, "g"), ("Parmezan", 80, "g"), ("Jaja", 3, "piece"), ("Beli luk", 12, "g"), ("Majonez", 120, "g"), ("Pavlaka", 150, "g"), ("Senf", 15, "g"), ("Limun", 80, "g"), ("Maslinovo ulje", 40, "g"), ("So", 5, "g"), ("Biber", 3, "g")],
    "Čokoladni griz": [("Mleko", 1000, "ml"), ("Griz", 160, "g"), ("Šećer", 120, "g"), ("Čokolada", 100, "g"), ("Vanila", 5, "g")],
    "Pirinač sa jajima": [("Pirinač", 400, "g"), ("Jaja", 5, "piece"), ("Luk", 150, "g"), ("Paprika", 200, "g")],
    "Pečurke sa pirinčem": [("Pečurke", 600, "g"), ("Pirinač", 350, "g"), ("Luk", 150, "g"), ("Šargarepa", 200, "g")],
    "Kuvani krompir sa sirom": [("Krompir", 1000, "g"), ("Sir", 250, "g"), ("Grčki jogurt", 200, "g")],
    "Junetina sa pečurkama": [("Junetina", 650, "g"), ("Pečurke", 450, "g"), ("Luk", 150, "g"), ("Krompir", 700, "g")],
    "Jaja sa šunkom": [("Jaja", 5, "piece"), ("Šunka", 250, "g"), ("Sir", 120, "g"), ("Paradajz", 200, "g")],
    "Pohovana piletina": [("Piletina", 700, "g"), ("Jaja", 3, "piece"), ("Brašno", 200, "g"), ("Krompir", 700, "g")],
    "Povrće iz rerne": [("Tikvica", 400, "g"), ("Paprika", 300, "g"), ("Krompir", 700, "g"), ("Paradajz", 300, "g")],
    "Povrtni wok": [("Tikvica", 350, "g"), ("Paprika", 300, "g"), ("Šargarepa", 250, "g"), ("Pečurke", 250, "g")],
    "Pileće rolnice sa sirom": [("Piletina", 650, "g"), ("Sir", 220, "g"), ("Spanać", 200, "g"), ("Krompir", 700, "g")],
    "Pileći file u rerni": [("Piletina", 700, "g"), ("Krompir", 800, "g"), ("Paprika", 250, "g"), ("Tikvica", 250, "g")],
    "Pileći ražnjići": [("Piletina", 650, "g"), ("Paprika", 300, "g"), ("Tikvica", 300, "g"), ("Luk", 180, "g")],
    "Piletina u paradajz sosu": [("Piletina", 600, "g"), ("Paradajz", 500, "g"), ("Luk", 150, "g"), ("Testenina", 350, "g")],
    "Pileća salata": [("Piletina", 450, "g"), ("Zelena salata", 250, "g"), ("Paradajz", 250, "g"), ("Paprika", 200, "g")],
    "Sendvič sa piletinom": [("Hleb", 350, "g"), ("Piletina", 400, "g"), ("Sir", 150, "g"), ("Paradajz", 200, "g")],
    "Tuna salata": [("Tunjevina", 350, "g"), ("Zelena salata", 250, "g"), ("Paradajz", 250, "g"), ("Paprika", 200, "g")],
    "Krompir salata": [("Krompir", 900, "g"), ("Luk", 150, "g"), ("Paprika", 200, "g"), ("Zelena salata", 150, "g")],
    "Kupus salata": [("Kupus", 800, "g"), ("Šargarepa", 200, "g"), ("Paradajz", 200, "g")],
    "Salata sa grilovanim povrćem": [("Tikvica", 350, "g"), ("Paprika", 300, "g"), ("Paradajz", 300, "g"), ("Sir", 150, "g")],
    "Svinjetina sa kupusom": [("Svinjetina", 650, "g"), ("Kupus", 800, "g"), ("Luk", 150, "g")],
    "Svinjetina sa povrćem": [("Svinjetina", 650, "g"), ("Paprika", 250, "g"), ("Tikvica", 300, "g"), ("Šargarepa", 200, "g")],
    "Svinjetina u sosu od pečuraka": [("Svinjetina", 650, "g"), ("Pečurke", 450, "g"), ("Mleko", 250, "g"), ("Krompir", 700, "g")],
    "Svinjske rolnice": [("Svinjetina", 650, "g"), ("Sir", 200, "g"), ("Spanać", 200, "g"), ("Krompir", 700, "g")],
    "Tikvice sa sirom": [("Tikvica", 700, "g"), ("Sir", 250, "g"), ("Jaja", 3, "piece"), ("Paradajz", 250, "g")],
    "Piletina u tortilji": [("Piletina", 500, "g"), ("Tortilja", 4, "piece"), ("Sir", 150, "g"), ("Paprika", 250, "g")],
    "Proteinska tortilja": [("Tortilja", 4, "piece"), ("Piletina", 450, "g"), ("Grčki jogurt", 200, "g"), ("Spanać", 150, "g")],
    "Tuna wrap": [("Tortilja", 4, "piece"), ("Tunjevina", 350, "g"), ("Zelena salata", 200, "g"), ("Paradajz", 250, "g")],
    "Pileći wrap": [("Tortilja", 4, "piece"), ("Piletina", 450, "g"), ("Zelena salata", 200, "g"), ("Paradajz", 250, "g")],
    "Quesadilla sa piletinom": [("Tortilja", 4, "piece"), ("Piletina", 450, "g"), ("Sir", 200, "g"), ("Paprika", 250, "g")],
    "Tuna punjene paprike": [("Tunjevina", 350, "g"), ("Paprika", 700, "g"), ("Pirinač", 250, "g"), ("Luk", 120, "g")],
    "Tuna rižoto": [("Tunjevina", 350, "g"), ("Pirinač", 300, "g"), ("Paradajz", 250, "g"), ("Luk", 120, "g")],
    "Tuna rice bowl": [("Tunjevina", 350, "g"), ("Pirinač", 300, "g"), ("Spanać", 200, "g"), ("Paradajz", 250, "g")],
    "Tuna salata sa jajima": [("Tunjevina", 350, "g"), ("Jaja", 4, "piece"), ("Zelena salata", 200, "g"), ("Paradajz", 250, "g")],
    "Losos sa povrćem": [("Losos", 600, "g"), ("Brokoli", 300, "g"), ("Tikvica", 300, "g"), ("Šargarepa", 200, "g")],
    "Losos salata": [("Losos", 500, "g"), ("Zelena salata", 250, "g"), ("Paradajz", 250, "g"), ("Spanać", 150, "g")],
    "Pastrmka iz rerne": [("Pastrmka", 700, "g"), ("Krompir", 800, "g"), ("Limun", 120, "g")],
    "Pastrmka sa krompirom": [("Pastrmka", 700, "g"), ("Krompir", 800, "g"), ("Blitva", 250, "g")],
    "Riba sa blitvom": [("Oslić", 700, "g"), ("Blitva", 350, "g"), ("Krompir", 700, "g")],
    "Riblja čorba": [("Oslić", 700, "g"), ("Luk", 180, "g"), ("Paprika", 250, "g"), ("Šargarepa", 200, "g")],
    "Oslić u paradajz sosu": [("Oslić", 700, "g"), ("Paradajz", 500, "g"), ("Luk", 150, "g"), ("Krompir", 700, "g")],
    "Piletina sa brokolijem": [("Piletina", 600, "g"), ("Brokoli", 450, "g"), ("Pirinač", 300, "g")],
    "Piletina sa graškom": [("Piletina", 600, "g"), ("Grašak", 500, "g"), ("Šargarepa", 200, "g"), ("Luk", 150, "g")],
    "Piletina sa sočivom": [("Piletina", 600, "g"), ("Sočivo", 350, "g"), ("Šargarepa", 200, "g"), ("Luk", 150, "g")],
    "Piletina sa spanaćem": [("Piletina", 600, "g"), ("Spanać", 350, "g"), ("Pirinač", 300, "g")],
    "Piletina sa susamom": [("Piletina", 600, "g"), ("Susam", 60, "g"), ("Paprika", 250, "g"), ("Pirinač", 300, "g")],
    "Piletina sa limunom": [("Piletina", 600, "g"), ("Limun", 150, "g"), ("Krompir", 800, "g"), ("Tikvica", 250, "g")],
    "Piletina sa medom i senfom": [("Piletina", 600, "g"), ("Med", 50, "g"), ("Senf", 50, "g"), ("Krompir", 800, "g")],
    "Piletina terijaki": [("Piletina", 600, "g"), ("Soja sos", 80, "g"), ("Paprika", 250, "g"), ("Pirinač", 300, "g")],
    "Piletina u sosu od pečuraka": [("Piletina", 600, "g"), ("Pečurke", 450, "g"), ("Mleko", 250, "g"), ("Pirinač", 300, "g")],
    "Brzi pileći wok": [("Piletina", 500, "g"), ("Paprika", 250, "g"), ("Tikvica", 250, "g"), ("Pirinač", 250, "g")],
    "Pileći kari": [("Piletina", 600, "g"), ("Paprika", 250, "g"), ("Šargarepa", 200, "g"), ("Pirinač", 300, "g")],
    "Pileća supa sa rezancima": [("Piletina", 500, "g"), ("Testenina", 180, "g"), ("Šargarepa", 200, "g"), ("Luk", 150, "g")],
    "Juneći rižoto": [("Junetina", 600, "g"), ("Pirinač", 300, "g"), ("Pečurke", 250, "g"), ("Luk", 150, "g")],
    "Juneći wok": [("Junetina", 600, "g"), ("Paprika", 250, "g"), ("Tikvica", 250, "g"), ("Pirinač", 250, "g")],
    "Grčki jogurt proteinska činija": [("Grčki jogurt", 600, "g"), ("Ovsene pahuljice", 160, "g"), ("Banana", 250, "g"), ("Jabuka", 250, "g")],
    "Jaja i sir fit tanjir": [("Jaja", 5, "piece"), ("Sir", 180, "g"), ("Paradajz", 250, "g"), ("Spanać", 150, "g")],
    "Junetina fit tanjir": [("Junetina", 600, "g"), ("Brokoli", 300, "g"), ("Krompir", 700, "g")],
    "Ćuretina sa tikvicama": [("Ćuretina", 600, "g"), ("Tikvica", 400, "g"), ("Paprika", 250, "g"), ("Pirinač", 250, "g")],
    "Ćureće ćufte": [("Ćuretina", 600, "g"), ("Jaja", 2, "piece"), ("Luk", 150, "g"), ("Paradajz", 350, "g")],
    "Boranija sa krompirom": [("Boranija", 700, "g"), ("Krompir", 700, "g"), ("Luk", 150, "g"), ("Šargarepa", 200, "g")],
    "Karfiol iz rerne": [("Karfiol", 800, "g"), ("Sir", 200, "g"), ("Jaja", 3, "piece")],
    "Krompir sa spanaćem": [("Krompir", 900, "g"), ("Spanać", 350, "g"), ("Sir", 150, "g")],
    "Povrtni kuskus": [("Kuskus", 350, "g"), ("Paprika", 250, "g"), ("Tikvica", 300, "g"), ("Šargarepa", 200, "g")],
    "Pohovane tikvice": [("Tikvica", 800, "g"), ("Jaja", 3, "piece"), ("Brašno", 180, "g"), ("Sir", 150, "g")],
    "Povrtne pljeskavice": [("Tikvica", 400, "g"), ("Šargarepa", 300, "g"), ("Jaja", 3, "piece"), ("Ovsene pahuljice", 160, "g")],
    "Krem čorba od pečuraka": [("Pečurke", 600, "g"), ("Krompir", 400, "g"), ("Luk", 150, "g"), ("Mleko", 250, "g")],
    "Pasta sa sirom": [("Testenina", 400, "g"), ("Sir", 250, "g"), ("Mleko", 250, "g")],
    "Pizza tost": [("Hleb", 350, "g"), ("Paradajz", 300, "g"), ("Sir", 250, "g"), ("Šunka", 200, "g")],
    "Tost sa sirom i paradajzom": [("Hleb", 350, "g"), ("Sir", 220, "g"), ("Paradajz", 300, "g")],
    "Sendvič sa jajima": [("Hleb", 350, "g"), ("Jaja", 5, "piece"), ("Sir", 120, "g"), ("Paradajz", 200, "g")],
    "Proteinski sendvič": [("Hleb", 350, "g"), ("Piletina", 400, "g"), ("Grčki jogurt", 150, "g"), ("Spanać", 150, "g")],
    "Prženi pirinač": [("Pirinač", 400, "g"), ("Jaja", 4, "piece"), ("Paprika", 200, "g"), ("Grašak", 250, "g")],
    "Brzi rižoto": [("Pirinač", 350, "g"), ("Pečurke", 250, "g"), ("Paradajz", 250, "g"), ("Sir", 150, "g")],
    "Grašak sa mesom": [("Mleveno meso", 500, "g"), ("Grašak", 600, "g"), ("Krompir", 600, "g"), ("Šargarepa", 200, "g")],
    "Domaća supa sa knedlama": [("Piletina", 500, "g"), ("Šargarepa", 250, "g"), ("Luk", 150, "g"), ("Brašno", 120, "g"), ("Jaja", 2, "piece")],
    "Kačamak sa kajmakom": [("Kukuruzno brašno", 300, "g"), ("Kajmak", 250, "g"), ("Sir", 150, "g")],
    "Gomboce sa šljivama": [("Krompir", 800, "g"), ("Brašno", 300, "g"), ("Šljiva", 500, "g"), ("Šećer", 100, "g")],
    "Uštipci": [("Brašno", 400, "g"), ("Mleko", 300, "g"), ("Jaja", 2, "piece"), ("Sir", 180, "g")],
    "Griz na mleku": [("Griz", 160, "g"), ("Mleko", 800, "g"), ("Šećer", 100, "g")],
    "Sutlijaš": [("Pirinač", 250, "g"), ("Mleko", 900, "g"), ("Šećer", 120, "g")],
    "Keks torta": [("Keks", 500, "g"), ("Mleko", 500, "g"), ("Grčki jogurt", 400, "g"), ("Banana", 300, "g")],
    "Ovseni kolač sa jabukom": [("Ovsene pahuljice", 250, "g"), ("Jabuka", 500, "g"), ("Jaja", 3, "piece"), ("Grčki jogurt", 200, "g")],
    "Voćna salata": [("Banana", 300, "g"), ("Jabuka", 350, "g"), ("Grčki jogurt", 250, "g")],
    "Salata od cvekle": [("Cvekla", 700, "g"), ("Sir", 180, "g"), ("Zelena salata", 150, "g")],
    "Salata od leblebija": [("Leblebije", 500, "g"), ("Paradajz", 300, "g"), ("Paprika", 200, "g"), ("Sir", 150, "g")],
    "Salata od pasulja": [("Pasulj", 500, "g"), ("Paprika", 250, "g"), ("Luk", 120, "g"), ("Paradajz", 250, "g")],
    "Salata sa kinoom": [("Kinoa", 300, "g"), ("Paradajz", 300, "g"), ("Paprika", 200, "g"), ("Sir", 150, "g")],
    "Salata sa testeninom": [("Testenina", 350, "g"), ("Paradajz", 300, "g"), ("Paprika", 200, "g"), ("Sir", 150, "g")],
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


def required_ingredients_for_title(recipe):
    """Minimum name-to-ingredient contract used to catch profile mistakes."""
    title = normalised_title(recipe)
    requirements = []
    checks = (
        (("piletina", "pileći", "pileća"), "Piletina"),
        (("junetina", "juneći", "juneća", "goveđi", "beef"), "Junetina"),
        (("svinjetina", "svinjski", "svinjske", "krmenadle"), "Svinjetina"),
        (("ćuretina", "ćureći", "ćureće"), "Ćuretina"),
        (("tuna", "tunjevin"), "Tunjevina"),
        (("losos",), "Losos"), (("pastrmka",), "Pastrmka"),
        (("oslić",), "Oslić"), (("tortilj", "wrap", "quesadilla"), "Tortilja"),
        (("brokoli",), "Brokoli"), (("spanać",), "Spanać"), (("grašak",), "Grašak"),
        (("sočivo",), "Sočivo"), (("pečurk",), "Pečurke"), (("tikvic",), "Tikvica"),
        (("karfiol",), "Karfiol"), (("boranija",), "Boranija"), (("kuskus",), "Kuskus"),
        (("cvekl",), "Cvekla"), (("leblebij",), "Leblebije"), (("kino",), "Kinoa"),
        (("kupus", "sarma", "podvarak"), "Kupus"), (("krompir",), "Krompir"),
        (("pirinač", "rižoto", "rice", "đuveč", "sutlijaš"), "Pirinač"),
        (("testen", "pasta", "špaget", "lazanj"), "Testenina"),
        (("paprikaš", "gulaš"), "Paprika"), (("kari",), "Kari"),
        (("pohovan", "pohovane", "pohovana"), "Prezle"),
        (("burger", "sendvič", "tost"), "Hleb"),
        (("palačinke",), "Jaja"), (("omlet", "jaja"), "Jaja"),
        (("sir", "gibanica"), "Sir"), (("kačamak", "palenta", "proja"), "Kukuruzno brašno"),
        (("ovsena",), "Ovsene pahuljice"), (("puding",), "Grčki jogurt"),
        (("jabuk",), "Jabuka"), (("banana",), "Banana"), (("šljiv",), "Šljiva"),
    )
    for needles, ingredient in checks:
        if has(title, *needles):
            requirements.append(ingredient)
    return requirements


def completed_ingredient_lines(recipe, profile, main_lines):
    """Add sensible pantry ingredients that used to be missing from every list."""
    title = normalised_title(recipe)
    present = {name for name, _, _ in main_lines}
    additions = []

    def add(name, quantity, unit="g"):
        if name not in present:
            additions.append((name, quantity, unit))
            present.add(name)

    # The exact named component belongs in the recipe even when an older broad
    # profile did not know about it (for example, breadcrumbs in a breaded dish).
    named_components = (
        (("paprikaš", "gulaš"), "Paprika", 200, "g"),
        (("paprikaš", "gulaš"), "Aleva paprika", 8, "g"),
        (("kari",), "Kari", 8, "g"),
        (("pohovan", "pohovane", "pohovana"), "Prezle", 180, "g"),
        (("burger", "sendvič", "tost"), "Hleb", 300, "g"),
    )
    for words, name, quantity, unit in named_components:
        if has(title, *words):
            add(name, quantity, unit)

    sweet = has(
        title, "kolač", "torta", "mafin", "koh", "palač", "griz", "sutlijaš", "puding", "hleb",
        "gomboce", "uštipci", "pita sa jabuk", "voćna salata", "ovsena kaša", "jogurt sa voćem",
        "proteinska ovsena", "grčki jogurt proteinska činija",
    )
    salad = "salata" in title
    soup_or_stew = has(title, "supa", "čorba", "gulaš", "paprikaš", "pasulj", "sočivo", "sarma", "podvarak", "kupus")

    if sweet:
        add("So", 2)
        add("Cimet", 3)
        if "pita sa jabuk" in title:
            add("Maslinovo ulje", 80)
            add("Prašak za pecivo", 8)
        if has(title, "kolač", "mafin", "hleb", "koh", "palač", "uštipci"):
            add("Prašak za pecivo", 10)
        if has(title, "griz", "sutlijaš", "puding", "koh", "torta"):
            add("Vanila", 5)
    elif salad:
        add("Maslinovo ulje", 30)
        add("Limun", 60)
        add("So", 5)
        add("Biber", 2)
        if "cezar" in title:
            add("Hleb", 120)
            add("Majonez", 100)
            add("Beli luk", 10)
            add("Slanina", 120)
    elif soup_or_stew:
        add("Maslinovo ulje", 30)
        add("So", 8)
        add("Biber", 3)
        add("Beli luk", 12)
        add("Aleva paprika", 8)
        if has(title, "sarma", "pasulj", "sočivo", "gulaš", "paprikaš", "kupus"):
            add("Lovorov list", 2, "piece")
    else:
        add("Maslinovo ulje", 25)
        add("So", 6)
        add("Biber", 3)
        if not has(title, "tost", "sendvič", "wrap", "tortilj", "bowl", "činija", "tanjir"):
            add("Beli luk", 10)

    # Additional technique-dependent ingredients.  These make broadly named
    # recipes cookable without inventing an unrelated main component.
    if has(title, "supa", "čorba"):
        add("Šargarepa", 200)
        add("Voda", 1500, "ml")
        add("Peršun", 15)
    if has(title, "faširane", "ćufte", "pljeskavice", "burger"):
        add("Jaja", 1, "piece")
        add("Prezle", 100)
    if has(title, "pohovan", "pohovane", "pohovana"):
        add("Jaja", 2, "piece")
        add("Brašno", 150)
        add("Prezle", 180)
    if has(title, "rolnice"):
        add("Sir", 150)
    if has(title, "sosu"):
        add("Pavlaka", 200, "ml")
    if has(title, "pita", "gibanica") and not has(title, "pita sa jabuk"):
        add("Maslinovo ulje", 70)
        add("Voda", 180, "ml")
    if has(title, "satar", "đuveč"):
        add("Luk", 150)
        add("Beli luk", 10)
    if has(title, "grilovan", "ražnjići"):
        add("Limun", 80)
    if has(title, "jaja na oko"):
        add("Paradajz", 250)
    if has(title, "omlet"):
        add("Maslinovo ulje", 15)
    return main_lines + additions


def style_for(recipe, profile):
    title = normalised_title(recipe)
    if has(title, "sarma", "punjene paprike"):
        return "stuffed"
    if has(title, "lazanj", "musaka"):
        return "layers"
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


def signature_step(recipe):
    """The recipe-specific action which prevents one generic method per type."""
    title = normalised_title(recipe)
    rules = (
        (("terijaki",), "Pred kraj dodajte sos u stilu terijakija i mešajte samo koliko je potrebno da obloži zalogaje."),
        (("kari",), "Za kari, kratko zapecite začine pre nego što nalijete tečnost, kako bi jelo dobilo puniji miris."),
        (("susam",), "Susam dodajte na samom kraju, kada je tiganj sklonjen sa najjače vatre, da ostane aromatičan."),
        (("medom i senfom",), "Premaz od meda i senfa nanesite tek pred kraj pečenja da se ne karamelizuje prerano."),
        (("limunom",), "Limun dodajte neposredno pred serviranje kako bi ostao svež, a ne gorak."),
        (("sosu od pečuraka",), "Pečurke najpre pustite da ispare višak tečnosti, pa tek onda sjedinite sos sa glavnim sastojkom."),
        (("paradajz sosu",), "Paradajz kuvajte dok se sos malo ne zgusne pre nego što dodate glavni sastojak."),
        (("rolnice",), "Nadev rasporedite ravnomerno, uvijte čvrsto i završetak rolnice položite nadole pri pečenju."),
        (("ražnjići",), "Komade poređajte na ražnjiće s malim razmakom, pa ih okrećite da se ispeku sa svih strana."),
        (("pohovan", "pohovane", "pohovana"), "Za pohovanje, svaki komad prvo uvaljajte u suvi deo, zatim u umućeno jaje i na kraju pažljivo ispecite."),
        (("pljeskavice", "burger"), "Oblikujte jednake pljeskavice bez preteranog pritiskanja, pa ih pecite dok ne dobiju koricu."),
        (("ćufte",), "Od smese oblikujte jednake ćufte vlažnim rukama, pa ih kratko zapecite pre završnog kuvanja."),
        (("šnicle", "krmenadle"), "Meso ispecite u jednoj turi bez pretrpavanja tiganja, kako bi dobilo boju umesto da se kuva u sopstvenom soku."),
        (("wok",), "Wok ili najširi tiganj dobro zagrejte; sastojke dodajte redom od onih koji se najduže spremaju ka najmekšima."),
        (("meal prep",), "Gotovo jelo podelite u odvojene posude tek kada se prohladi, kako bi ostalo prijatno i narednog dana."),
        (("bowl", "činija", "tanjir"), "Komponente rasporedite odvojeno u činiji, a preliv ili začine dodajte tik pred jelo."),
        (("cezar",), "Za cezar salatu, topli protein položite preko hladne salate neposredno pre serviranja da listovi ostanu hrskavi."),
        (("grčka salata", "šopska salata", "mediteranska salata"), "Povrće seckajte krupnije i začinite neposredno pred serviranje da ne pusti previše soka."),
        (("krompir salata",), "Krompir ohladite do mlakog pre sjedinjavanja kako bi zadržao oblik u salati."),
        (("salata od pasulja",), "Pasulj prethodno dobro ocedite i ohladite, pa ga nežno sjedinite s prelivom da se ne zgnječi."),
        (("salata od testeninom", "salata sa testeninom"), "Testeninu ohladite i osušite pre mešanja kako preliv ne bi postao vodenast."),
        (("palačinke",), "Ostavite smesu za palačinke nekoliko minuta da odmori, zatim pecite tanke palačinke na umereno zagrejanom tiganju."),
        (("mafine",), "Smesu za mafine samo kratko sjedinite, rasporedite do dve trećine kalupa i pecite dok čačkalica ne izađe suva."),
        (("banana hleb",), "Banane izgnječite viljuškom, suve sastojke umešajte kratko i pecite u kalupu dok sredina ne bude suva na čačkalici."),
        (("puding",), "Smesu neprekidno mešajte na tihoj vatri dok se ne zgusne, zatim je ohladite pre serviranja."),
        (("keks torta",), "Slojeve slažite u hladnoj posudi i ostavite najmanje nekoliko sati da keks omekša i torta se stegne."),
        (("koh",), "Pečen koh prelijte toplim mlekom postepeno, pa ga ostavite da ravnomerno upije tečnost."),
        (("gomboce",), "Knedle spuštajte u blago ključalu vodu i vadite ih kada isplivaju; tada ih uvaljajte u pripremljeni posip."),
        (("pita sa jabukama",), "Jabuke kratko ocedite pre slaganja da pita ostane hrskava, a ne vlažna."),
        (("griz", "sutlijaš", "kaša", "kačamak", "palenta"), "Suv sastojak sipajte postepeno uz stalno mešanje kako se ne bi napravile grudvice."),
        (("pizza tost",), "Tost kratko zapecite dok sir ne počne da se topi, ali ga ne ostavljajte predugo da hleb ne postane tvrd."),
        (("quesadilla",), "Tortilju pecite preklopljenu na srednjoj vatri i pažljivo okrenite kada donja strana postane zlatna."),
        (("wrap", "tortilji", "tortilja"), "Punjenje ohladite minut-dva, savijte bočne strane tortilje ka unutra i čvrsto je zarolajte."),
        (("sendvič", "tost"), "Hleb kratko zapecite odvojeno, pa sastojke složite neposredno pre serviranja da ostane hrskav."),
        (("rižoto",), "Tečnost dodajte postepeno uz često mešanje, tako da pirinač postane kremast, ali zadrži oblik zrna."),
        (("prženi pirinač",), "Koristite ohlađen pirinač i pržite ga na jačoj vatri u manjim turama da ostane rastresit."),
        (("đuveč",), "Pecite poklopljeno dok pirinač ne omekša, zatim poslednjih nekoliko minuta otklopite da višak tečnosti ispari."),
        (("sup", "čorb"), "Po potrebi skidajte penu sa površine i kuvajte na tihom ključanju da supa ili čorba ostane bistra."),
        (("pasulj",), "Pasulj prethodno potopite preko noći kada je suv; kuvajte ga lagano dok zrna ne postanu potpuno mekana."),
        (("sočivo",), "Sočivo isperite pre kuvanja i dodajte ga kada se aromatično povrće već omekša, jer se brže skuva od pasulja."),
        (("prebranac",), "Pasulj i luk složite u plitku posudu, pa zapecite dok vrh ne dobije tamniju, slatkastu koricu."),
        (("sarma",), "Listove kupusa rasporedite tako da otvor bude okrenut nadole; kuvajte tiho da se sarme ne otvore."),
        (("podvarak", "kupus sa mesom", "svadbarski kupus"), "Kupus i meso pecite poklopljeno dok ne omekšaju, a zatim kratko otklopite da se površina zapeče."),
        (("file u rerni", "iz rerne", "u rerni", "pečena", "pečeni"), "Rernu zagrejte unapred i proverite deblji deo glavnog sastojka pre vađenja da bude potpuno gotov."),
        (("oslić", "pastrmka", "losos", "riba"), "Ribu pažljivo prevrnite samo jednom i završite čim se lako razdvaja viljuškom da ne postane suva."),
    )
    for needles, text in rules:
        if has(title, *needles):
            return text
    return f"Tokom pripreme proveravajte ukus i teksturu, jer je cilj da {recipe.title.lower()} ostane sočan i uravnotežen."


def instructions_for(recipe, profile, ingredients):
    """Create an individual, title-aware preparation that matches the dish type."""
    names = ingredient_names(ingredients)
    if not names:
        raise CommandError(f"Recept nema sastojke: {recipe.title}")
    first = names[0]
    rest = ", ".join(names[1:]) or first
    style = style_for(recipe, profile)
    prep = pick(recipe, [
        f"Operite i pripremite sastojke za jelo „{recipe.title}“; sve što se seče pripremite pre početka kuvanja.",
        f"Za jelo „{recipe.title}“ pripremite radnu površinu i odmerite {', '.join(names)}.",
        f"Prvo pripremite {', '.join(names)} kako bi priprema jela „{recipe.title}“ tekla bez prekida.",
    ])

    # These recipes need a real, dedicated sequence. Their title is not merely
    # a variation of a broad profile such as "porridge" or "cold salad".
    if "proteinski puding" in normalised_title(recipe):
        steps = [
            f"Za jelo „{recipe.title}“ izmiksajte {', '.join(names)} dok smesa ne postane potpuno glatka.",
            "Prebacite smesu u šerpicu i zagrevajte na tihoj vatri uz stalno mešanje, bez jakog ključanja.",
            "Kada se puding zgusne i obloži kašiku, sipajte ga u čaše i ostavite da se prohladi.",
            "Pokrijte i hladite najmanje 30 minuta, pa poslužite hladan.",
        ]
    elif "palačinke" in normalised_title(recipe):
        steps = [
            f"Za jelo „{recipe.title}“ usitnite ili izmiksajte {', '.join(names)} u glatku smesu.",
            "Ostavite smesu 10 minuta da odmori, dok zagrevate blago podmazan tiganj na srednjoj vatri.",
            "Sipajte tanki sloj smese, pecite dok se ivice ne odvoje, pa pažljivo okrenite i ispecite drugu stranu.",
            "Nastavite dok ne potrošite smesu i poslužite palačinke tople.",
        ]
    elif "cezar" in normalised_title(recipe):
        steps = [
            f"Za jelo „{recipe.title}“ ispecite {first} na umerenoj vatri dok ne bude potpuno pečen, pa ga ostavite 5 minuta da odmori.",
            "Zelenu salatu operite, dobro osušite i krupno iskidajte kako bi ostala hrskava.",
            f"U velikoj činiji sjedinite salatu sa preostalim sastojcima: {rest}.",
            "Narežite topli protein, rasporedite ga preko salate i začinite neposredno pre serviranja.",
        ]
    elif style == "cold":
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
    elif style == "stuffed":
        steps = [
            prep,
            "Pripremite nadjev tako što ćete sjediniti glavni sastojak sa sitno seckanim dodacima i začinima.",
            "Napunite povrće ili listove kupusa ravnomerno, bez previše punjenja, pa pažljivo složite u šerpu.",
            "Nalijte toplom vodom do visine punjenja, poklopite i kuvajte lagano dok nadjev i omotač ne omekšaju.",
            f"Ostavite {recipe.title.lower()} 10 minuta da odmori pre serviranja kako bi zadržao oblik.",
        ]
    elif style == "layers":
        steps = [
            prep,
            "Zagrejte rernu na 180°C i pripremite posudu za pečenje.",
            f"Prvo pripremite {first} sa sastojcima {rest}, tako da svi budu delimično omekšani.",
            "Ređajte sastojke u ravnim slojevima i završite slojem koji će tokom pečenja napraviti zlatnu koricu.",
            "Pecite dok sredina ne bude potpuno vruća i čvrsta, a površina lepo zapečena.",
            f"Ostavite {recipe.title.lower()} 10 minuta pre sečenja da se slojevi stabilizuju.",
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

    is_dedicated_method = any(word in normalised_title(recipe) for word in ("proteinski puding", "palačinke", "cezar"))

    # Every non-dedicated method also receives one concrete, dish-specific technique. This is
    # intentionally separate from the broad cooking-style instructions above.
    if not is_dedicated_method:
        steps.insert(1, signature_step(recipe))

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
        for name, values in EXTRA_INGREDIENTS.items():
            Ingredient.objects.get_or_create(
                name=name,
                defaults={
                    "slug": slugify(name), "category": values[0], "calories_per_100g": values[1],
                    "protein_per_100g": values[2], "carbs_per_100g": values[3],
                    "fat_per_100g": values[4], "fiber_per_100g": values[5],
                },
            )
        for recipe in Recipe.objects.prefetch_related("recipe_ingredients__ingredient"):
            profile = profile_for(recipe)
            main_lines = TITLE_INGREDIENTS.get(recipe.title, PROFILE_OVERRIDES.get(recipe.title, PROFILES[profile]))
            ingredient_lines = completed_ingredient_lines(recipe, profile, main_lines)
            # The command owns generated data, so rewrite it fully. This avoids
            # stale category-profile ingredients remaining on a renamed dish.
            recipe.recipe_ingredients.all().delete()
            if not recipe.recipe_ingredients.exists():
                for name, quantity, unit in ingredient_lines:
                    ingredient = Ingredient.objects.get(name=name)
                    _, made = RecipeIngredient.objects.get_or_create(
                        recipe=recipe,
                        ingredient=ingredient,
                        defaults={"quantity": quantity, "unit": unit},
                    )
                    added_lines += int(made)
            lines = list(recipe.recipe_ingredients.select_related("ingredient"))
            present = {line.ingredient.name for line in lines}
            missing = [name for name in required_ingredients_for_title(recipe) if name not in present]
            if missing:
                raise CommandError(
                    f"Naziv i sastojci nisu usklađeni za '{recipe.title}': nedostaje {', '.join(missing)}"
                )
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
