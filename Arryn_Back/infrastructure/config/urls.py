from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("Arryn_Back.infrastructure.api.urls")),  # <- Aquí incluyes las urls de tu app
]
