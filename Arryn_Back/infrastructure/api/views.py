import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from bson import ObjectId
from pymongo import ASCENDING

from .models import User
from .serializer import UserSerializer
from ...domain.services.mongo_service import (
    guardar_json,
    obtener_json,
    obtener_por_id,
    obtener_marcas,
    obtener_categorias,
    db,
)
from ...domain.services.parse_details import parse_details
from ...domain.services.price_service import PricePersonalizationService
from ...domain.services.ranking_service import OfferRankingService
from ...domain.services.report_service import ReportService


class ArchivosJsonView(APIView):
    def post(self, request):
        try:
            raw_body = request.body.decode("utf-8").strip()

            # Si viene como un JSON normal (objeto o lista)
            try:
                data = json.loads(raw_body)
                docs = data if isinstance(data, list) else [data]
            except json.JSONDecodeError:
                # Si falla, asumimos que son múltiples JSONs separados por saltos de línea
                docs = [json.loads(line) for line in raw_body.splitlines() if line.strip()]

            ids = guardar_json("archivos", docs)
            return Response(
                {"mensaje": "Guardado en Mongo", "ids": ids},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def get(self, request):
        docs = obtener_json("archivos")
        return Response(docs, status=status.HTTP_200_OK)
    
    
@api_view(['GET'])
def getUsers(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def createUser(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # Handle case where user might be a list or single object
        user_id = user[0].id if isinstance(user, list) else user.id
        username = serializer.validated_data.get("username") if serializer.validated_data else None
        return Response(
            {"message": "Usuario creado correctamente", "id": user_id, "username": username},
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
@api_view(['GET', 'PUT', 'DELETE'])
def userDetail(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class DetallesAdicionalesView(APIView):
    def get(self, request):
        docs = obtener_json("archivos")

        resultados = []
        for doc in docs:
            if "detalles_adicionales" in doc:
                detalles_json = parse_details(doc["detalles_adicionales"])
                resultados.append({
                    "titulo": doc.get("titulo", "Sin título"),
                    "detalles_adicionales": detalles_json
                })

        return Response(resultados, status=status.HTTP_200_OK)
    

class DetallesPorIdView(APIView):
    def get(self, request, id):
        collection = db["archivos"]
        doc = collection.find_one({"_id": ObjectId(id)}, {"_id": 0})

        if not doc or "detalles_adicionales" not in doc:
            return Response({"error": "No se encontraron detalles adicionales"}, status=status.HTTP_404_NOT_FOUND)

        # Parsear los detalles como antes
        detalles_json = parse_details(doc["detalles_adicionales"])

        # Convertimos cada key:value en párrafos separados
        partes = []
        for k, v in detalles_json.items():
            if k.strip():  # si la clave no está vacía
                partes.append(f"{k}: {v}")
            else:  # si la clave está vacía, solo agregamos el valor
                partes.append(v)

        # Unir con saltos de línea dobles para formar párrafos
        detalles_final = "\n\n".join(partes)

        return Response({"detalles_adicionales": detalles_final}, status=status.HTTP_200_OK)
    
class BrandListView(APIView):
    def get(self, request):
        with_counts = str(request.query_params.get("with_counts", "false")).lower() in {"1","true","yes","y"}
        fuente = request.query_params.get("fuente")
        categoria = request.query_params.get("categoria")

        try:
            brands, counts = obtener_marcas(
                coleccion="archivos",
                with_counts=with_counts,
                fuente=fuente,
                categoria=categoria
            )
        except Exception as e:
            # Si MongoDB no está disponible, devolver datos de ejemplo
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                return Response({
                    "count": 0,
                    "brands": [],
                    "message": "MongoDB no disponible - datos de ejemplo",
                    "error": str(e)
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "detail": f"Error consultando Mongo: {e}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        payload = {"count": len(brands), "brands": brands}
        if with_counts:
            payload["counts"] = counts
        return Response(payload, status=status.HTTP_200_OK)

class CategoryListView(APIView):
    def get(self, request):
        try:
            categories = obtener_categorias("archivos")
            return Response(
                {
                    "count": len(categories),
                    "categories": categories,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": f"Error obteniendo categorías: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class OffersByCategoryView(APIView):
    """
    GET /offers/<category>/?limit=20
    Devuelve productos de la colección 'archivos' filtrados por categoría,
    ordenados por precio_valor ascendente.
    """
    DEFAULT_COLLECTION = "archivos"
    DEFAULT_LIMIT = 20

    def get(self, request, category: str):
        limit = request.query_params.get("limit", self.DEFAULT_LIMIT)

        try:
            limit = max(1, min(int(limit), 100))  # entre 1 y 100
        except ValueError:
            return Response({"error": "Parametro 'limit' inválido"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if db is not None:
                collection = db[self.DEFAULT_COLLECTION]
            else:
                raise Exception("MongoDB no disponible")
            cursor = (collection
                      .find({"categoria": category}, {
                          "_id": 1,
                          "titulo": 1,
                          "marca": 1,
                          "precio_texto": 1,
                          "precio_valor": 1,
                          "moneda": 1,
                          "categoria": 1,
                          "imagen": 1,
                          "link": 1,
                          "fuente": 1,
                          "fecha_extraccion": 1
                      })
                      .sort("precio_valor", ASCENDING)
                      .limit(limit))

            docs = list(cursor)
            for d in docs:
                d["_id"] = str(d["_id"])

            return Response({
                "category": category,
                "count": len(docs),
                "results": docs
            }, status=status.HTTP_200_OK)

        except Exception as e:
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                return Response({
                    "category": category,
                    "count": 0, 
                    "results": [],
                    "message": "MongoDB no disponible",
                    "error": str(e)
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": f"Error consultando Mongo: {e}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BestPricesView(APIView):
    """
    GET /best-prices/<category>/?user_id=123&limit=10
    Obtiene los mejores precios personalizados por categoría
    """
    def get(self, request, category: str):
        user_id = request.query_params.get("user_id")
        limit = int(request.query_params.get("limit", 10))
        
        # Obtener preferencias del usuario desde base de datos o configuración
        user_preferences = None
        if user_id:
            # En el futuro esto vendría de la base de datos del usuario
            user_preferences = {
                "marcas_favoritas": ["NIKE", "ADIDAS"],
                "precio_max": 200,
                "precio_min": 50
            }
        
        try:
            results = PricePersonalizationService.get_best_prices_by_category(
                categoria=category,
                user_preferences=user_preferences,
                limit=limit
            )
            
            return Response({
                "category": category,
                "user_id": user_id,
                "personalized": user_preferences is not None,
                "count": len(results),
                "results": results
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "error": f"Error obteniendo mejores precios: {e}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PriceComparisonView(APIView):
    """
    GET /price-comparison/?product=iPhone
    Compara precios del mismo producto entre diferentes tiendas
    """
    def get(self, request):
        product = request.query_params.get("product")
        
        if not product:
            return Response({
                "error": "Parámetro 'product' es requerido"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            comparison = PricePersonalizationService.get_price_comparison(product)
            return Response(comparison, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "error": f"Error comparando precios: {e}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RankedOffersView(APIView):
    """
    GET /ranked-offers/?category=electronics&user_id=123&limit=20
    Obtiene ofertas rankeadas por valor
    """
    def get(self, request):
        category = request.query_params.get("category")
        user_id = request.query_params.get("user_id")
        limit = int(request.query_params.get("limit", 20))
        
        try:
            results = OfferRankingService.rank_offers_by_value(
                categoria=category,
                user_id=int(user_id) if user_id else None,
                limit=limit
            )
            
            return Response({
                "category": category,
                "user_id": user_id,
                "ranking_algorithm": "value_score",
                "count": len(results),
                "results": results
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "error": f"Error obteniendo ofertas rankeadas: {e}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TrendingOffersView(APIView):
    """
    GET /trending-offers/?days=7&limit=15
    Obtiene ofertas que están en tendencia
    """
    def get(self, request):
        days = int(request.query_params.get("days", 7))
        limit = int(request.query_params.get("limit", 15))
        
        try:
            results = OfferRankingService.get_trending_offers(
                timeframe_days=days,
                limit=limit
            )
            
            return Response({
                "timeframe_days": days,
                "algorithm": "trending_score",
                "count": len(results),
                "results": results
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "error": f"Error obteniendo ofertas trending: {e}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StoreComparisonReportView(APIView):
    """
    GET /reports/store-comparison/?category=electronics&days=30
    Genera reporte de comparación entre tiendas
    """
    def get(self, request):
        category = request.query_params.get("category")
        days = int(request.query_params.get("days", 30))
        
        try:
            report = ReportService.generate_store_comparison_report(
                categoria=category,
                days_back=days
            )
            
            return Response(report, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "error": f"Error generando reporte de tiendas: {e}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PriceAnalysisReportView(APIView):
    """
    GET /reports/price-analysis/<category>/?days=30
    Genera análisis de precios por categoría
    """
    def get(self, request, category: str):
        days = int(request.query_params.get("days", 30))
        
        try:
            report = ReportService.generate_price_analysis_report(
                categoria=category,
                days_back=days
            )
            
            return Response(report, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "error": f"Error generando análisis de precios: {e}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
