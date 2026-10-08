from django.urls import path
from . import views
app_name = "users"
urlpatterns = [path("registracija/", views.register, name="register"), path("kontrolna-tabla/", views.dashboard, name="dashboard")]
