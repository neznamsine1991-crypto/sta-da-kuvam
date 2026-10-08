from django.db import models
from recipes.models import Ingredient
class Supermarket(models.Model):
    name = models.CharField(max_length=80, unique=True); slug = models.SlugField(unique=True)
    website = models.URLField(blank=True); active = models.BooleanField(default=True)
    def __str__(self): return self.name
class IngredientPrice(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="prices")
    supermarket = models.ForeignKey(Supermarket, on_delete=models.CASCADE, related_name="prices")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Cena pakovanja u RSD")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Količina pakovanja")
    unit = models.CharField(max_length=12, default="g")
    valid_from = models.DateField(); valid_until = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=160, default="DEMO / ručni unos")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-valid_from"]; indexes = [models.Index(fields=["ingredient", "supermarket", "valid_from"])]
    @property
    def price_per_unit(self): return self.price / self.quantity if self.quantity else 0
    def __str__(self): return f"{self.ingredient} — {self.supermarket}"
