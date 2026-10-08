from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [("recipes", "0001_initial")]
    operations = [migrations.AddField(model_name="recipe", name="image_source", field=models.CharField(blank=True, max_length=80)), migrations.AddField(model_name="recipe", name="image_author", field=models.CharField(blank=True, max_length=160)), migrations.AddField(model_name="recipe", name="image_source_url", field=models.URLField(blank=True))]
