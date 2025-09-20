from django.urls import path
from .views import ArchivosJsonView, DetallesAdicionalesView, DetallesPorIdView, getUsers, createUser, userDetail, BrandListView

urlpatterns = [
    path("user/", getUsers, name="get_user"),
    path("user/create", createUser, name="create_user"),
    path("user/<int:pk>/", userDetail, name="user_detail"),
    path("archivos/", ArchivosJsonView.as_view(), name="archivos"),
    path("archivos/detalles/", DetallesAdicionalesView.as_view(), name="detalles_all"),
    path("archivos/<str:id>/detalles/", DetallesPorIdView.as_view(), name="detalles_por_id"),
    path("brands/", BrandListView.as_view(), name="brand-list"),
]
