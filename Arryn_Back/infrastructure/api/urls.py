from django.urls import path
from .views import (
    ArchivosJsonView, DetallesAdicionalesView, DetallesPorIdView, 
    getUsers, createUser, userDetail, BrandListView, OffersByCategoryView,
    BestPricesView, PriceComparisonView, RankedOffersView, TrendingOffersView,
    StoreComparisonReportView, PriceAnalysisReportView
)

urlpatterns = [
    path("user/", getUsers, name="get_user"),
    path("user/create", createUser, name="create_user"),
    path("user/<int:pk>/", userDetail, name="user_detail"),
    path("archivos/", ArchivosJsonView.as_view(), name="archivos"),
    path("archivos/detalles/", DetallesAdicionalesView.as_view(), name="detalles_all"),
    path("archivos/<str:id>/detalles/", DetallesPorIdView.as_view(), name="detalles_por_id"),
    path("brands/", BrandListView.as_view(), name="brand-list"),
    path("offers/<str:category>/", OffersByCategoryView.as_view(), name="offers_by_category"),
    
    # Nuevas funcionalidades
    path("best-prices/<str:category>/", BestPricesView.as_view(), name="best_prices"),
    path("price-comparison/", PriceComparisonView.as_view(), name="price_comparison"),
    path("ranked-offers/", RankedOffersView.as_view(), name="ranked_offers"),
    path("trending-offers/", TrendingOffersView.as_view(), name="trending_offers"),
    
    # Reportes
    path("reports/store-comparison/", StoreComparisonReportView.as_view(), name="store_comparison_report"),
    path("reports/price-analysis/<str:category>/", PriceAnalysisReportView.as_view(), name="price_analysis_report"),
]
