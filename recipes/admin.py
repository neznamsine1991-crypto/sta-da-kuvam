from django.contrib import admin
from .models import Category, Ingredient, Recipe, RecipeIngredient
class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient; extra = 1; autocomplete_fields = ("ingredient",)
@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "servings", "featured", "published")
    list_filter = ("category", "featured", "published"); search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}; inlines = [RecipeIngredientInline]
@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    search_fields = ("name",); prepopulated_fields = {"slug": ("name",)}
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin): prepopulated_fields = {"slug": ("name",)}
