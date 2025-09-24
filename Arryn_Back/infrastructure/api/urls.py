<<<<<<< HEAD
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
=======
from django.urls import path
from .views import ArchivosJsonView, DetallesAdicionalesView, DetallesPorIdView, getUsers, createUser, userDetail, BrandListView, OffersByCategoryView

urlpatterns = [
    path("user/", getUsers, name="get_user"),
    path("user/create", createUser, name="create_user"),
    path("user/<int:pk>/", userDetail, name="user_detail"),
    path("archivos/", ArchivosJsonView.as_view(), name="archivos"),
    path("archivos/detalles/", DetallesAdicionalesView.as_view(), name="detalles_all"),
    path("archivos/<str:id>/detalles/", DetallesPorIdView.as_view(), name="detalles_por_id"),
    path("brands/", BrandListView.as_view(), name="brand-list"),
    path("offers/<str:category>/", OffersByCategoryView.as_view(), name="offers_by_category"),

]
>>>>>>> origin/feature/SCRUM-125-Implementar-identificador-de-ofertas-por-categoría
