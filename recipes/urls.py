from django.urls import path
from . import views
app_name = "recipes"
urlpatterns = [path("", views.recipe_list, name="list"), path("kategorije/", views.category_list, name="categories"), path("kategorije/<slug:slug>/", views.category_detail, name="category_detail"), path("api/suggestions/", views.suggestions, name="suggestions"), path("<slug:slug>/", views.recipe_detail, name="detail"), path("<slug:slug>/omiljeno/", views.toggle_favorite, name="favorite")]
