"""Downloads attributed, freely licensed food images from Wikimedia Commons."""
import io, json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image
from recipes.models import Recipe

API = "https://commons.wikimedia.org/w/api.php?"
class Command(BaseCommand):
    help = "Pronalazi i lokalno čuva Commons slike za recepte kojima nedostaju slike."
    def handle(self, *args, **options):
        updated = failed = 0
        for recipe in Recipe.objects.filter(published=True, image=""):
            query = urlencode({"action":"query", "generator":"search", "gsrsearch":recipe.title + " food", "gsrnamespace":6, "gsrlimit":5, "prop":"imageinfo", "iiprop":"url|extmetadata", "iiurlwidth":900, "format":"json"})
            try:
                data = json.load(urlopen(Request(API + query, headers={"User-Agent":"StaDaKuvam/1.0"}), timeout=20))
                pages = data.get("query", {}).get("pages", {}).values()
                candidate = next((p for p in pages if p.get("imageinfo")), None)
                info = candidate["imageinfo"][0] if candidate else None
                if not info: raise ValueError("nema slike")
                raw = urlopen(Request(info.get("thumburl", info["url"]), headers={"User-Agent":"StaDaKuvam/1.0"}), timeout=30).read()
                image = Image.open(io.BytesIO(raw)).convert("RGB"); image.thumbnail((900, 650))
                output = io.BytesIO(); image.save(output, "JPEG", quality=84, optimize=True)
                recipe.image.save(recipe.slug + ".jpg", ContentFile(output.getvalue()), save=False)
                meta = info.get("extmetadata", {})
                recipe.image_alt = recipe.title; recipe.image_source = "Wikimedia Commons"
                recipe.image_author = meta.get("Artist", {}).get("value", "")[:160]
                recipe.image_source_url = "https://commons.wikimedia.org/wiki/" + candidate["title"].replace(" ", "_")
                recipe.save(); updated += 1
            except Exception as error:
                failed += 1; self.stderr.write(f"{recipe.title}: {error}")
        self.stdout.write(self.style.SUCCESS(f"Sačuvano: {updated}; neuspešno: {failed}."))
