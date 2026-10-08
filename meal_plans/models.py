from django.conf import settings
from django.db import models
class MealPlan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="meal_plans")
    name = models.CharField(max_length=100, default="Nedeljni plan")
    people = models.PositiveIntegerField(default=1); budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
class MealPlanItem(models.Model):
    MEALS = [("breakfast", "Doručak"), ("lunch", "Ručak"), ("dinner", "Večera")]
    meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE, related_name="items")
    recipe = models.ForeignKey("recipes.Recipe", on_delete=models.CASCADE)
    day = models.PositiveSmallIntegerField(default=1)
    meal = models.CharField(max_length=12, choices=MEALS)
    class Meta: unique_together = [("meal_plan", "day", "meal")]
