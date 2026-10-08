from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from recipes.views import home
urlpatterns = [path("admin/", admin.site.urls), path("", home, name="home"), path("recepti/", include("recipes.urls")), path("cene/", include("prices.urls")), path("kupovina/", include("shopping.urls")), path("plan/", include("meal_plans.urls")), path("nalog/", include("users.urls")), path("nalog/", include("django.contrib.auth.urls"))]
if settings.DEBUG: urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
