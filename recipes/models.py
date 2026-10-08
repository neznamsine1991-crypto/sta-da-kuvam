from django.db import models
from django.urls import reverse

class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)
    def __str__(self): return self.name

class Ingredient(models.Model):
    UNITS = [("g", "g"), ("ml", "ml"), ("piece", "kom")]
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(unique=True)
    category = models.CharField(max_length=60, blank=True)
    unit = models.CharField(max_length=12, choices=UNITS, default="g")
    calories_per_100g = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    protein_per_100g = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    carbs_per_100g = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    fat_per_100g = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    fiber_per_100g = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    class Meta: ordering = ["name"]
    def __str__(self): return self.name

class Recipe(models.Model):
    DIFFICULTIES = [("easy", "Lako"), ("medium", "Srednje"), ("hard", "Napredno")]
    title = models.CharField(max_length=180)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    instructions = models.TextField(help_text="Jedan korak po redu")
    prep_time = models.PositiveIntegerField(default=10)
    cook_time = models.PositiveIntegerField(default=20)
    servings = models.PositiveIntegerField(default=2)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="recipes")
    image = models.ImageField(upload_to="recipes/", blank=True)
    image_alt = models.CharField(max_length=160, blank=True)
    image_source = models.CharField(max_length=80, blank=True)
    image_author = models.CharField(max_length=160, blank=True)
    image_source_url = models.URLField(blank=True)
    calories = models.DecimalField(max_digits=8, decimal_places=1, default=0)
    protein = models.DecimalField(max_digits=8, decimal_places=1, default=0)
    carbohydrates = models.DecimalField(max_digits=8, decimal_places=1, default=0)
    fat = models.DecimalField(max_digits=8, decimal_places=1, default=0)
    fiber = models.DecimalField(max_digits=8, decimal_places=1, default=0)
    featured = models.BooleanField(default=False)
    published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-featured", "title"]
        indexes = [models.Index(fields=["published", "featured"])]
    @property
    def total_time(self): return self.prep_time + self.cook_time
    def get_absolute_url(self): return reverse("recipes:detail", args=[self.slug])
    def __str__(self): return self.title

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="recipe_ingredients")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, related_name="recipe_ingredients")
    quantity = models.DecimalField(max_digits=8, decimal_places=2)
    unit = models.CharField(max_length=12, choices=Ingredient.UNITS, default="g")
    optional = models.BooleanField(default=False)
    notes = models.CharField(max_length=120, blank=True)
    class Meta: unique_together = [("recipe", "ingredient")]
    def __str__(self): return f"{self.ingredient} — {self.quantity}{self.unit}"
