from django.urls import path
from . import views
app_name = "shopping"
urlpatterns = [path("", views.shopping_list, name="list"), path("dodaj/<slug:slug>/", views.add_recipe, name="add_recipe"), path("stavka/<int:pk>/", views.toggle_item, name="toggle")]
