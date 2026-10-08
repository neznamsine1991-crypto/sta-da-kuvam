from django.conf import settings
from django.db import models
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    diet_preference = models.CharField(max_length=50, blank=True)
    calorie_target = models.PositiveIntegerField(null=True, blank=True)
    protein_target = models.PositiveIntegerField(null=True, blank=True)
    budget_preference = models.PositiveIntegerField(null=True, blank=True)
    favorites = models.ManyToManyField("recipes.Recipe", blank=True, related_name="favorited_by")
from django.db.models.signals import post_save
from django.dispatch import receiver
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created: Profile.objects.create(user=instance)
