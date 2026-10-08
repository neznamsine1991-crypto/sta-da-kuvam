from django.contrib import admin
from .models import Supermarket, IngredientPrice
@admin.register(Supermarket)
class SupermarketAdmin(admin.ModelAdmin): prepopulated_fields = {"slug": ("name",)}
@admin.register(IngredientPrice)
class PriceAdmin(admin.ModelAdmin):
    list_display = ("ingredient", "supermarket", "price", "quantity", "unit", "valid_from")
    list_filter = ("supermarket",); autocomplete_fields = ("ingredient",)
