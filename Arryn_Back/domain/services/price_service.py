"""
Servicio para manejo de precios y personalización de ofertas
"""
from typing import List, Dict, Any, Optional
from .mongo_service import db, MONGO_AVAILABLE
from bson import ObjectId


class PricePersonalizationService:
    """Servicio para personalización de precios y ofertas"""
    
    @staticmethod
    def get_best_prices_by_category(
        categoria: str, 
        user_preferences: Optional[Dict] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtiene los mejores precios de una categoría con personalización
        
        Args:
            categoria: Categoría de productos
            user_preferences: Preferencias del usuario (marcas favoritas, rango de precios, etc.)
            limit: Número máximo de resultados
            
        Returns:
            Lista de productos con mejores precios
        """
        if not MONGO_AVAILABLE or db is None:
            return _get_mock_best_prices(categoria, limit)
        
        try:
            collection = db["archivos"]
            
            # Filtro base por categoría
            match_filter = {"categoria": categoria, "precio_valor": {"$exists": True, "$ne": None}}
            
            # Aplicar preferencias del usuario si existen
            if user_preferences:
                if "marcas_favoritas" in user_preferences:
                    match_filter["marca"] = {"$in": user_preferences["marcas_favoritas"]}
                
                if "precio_max" in user_preferences:
                    match_filter["precio_valor"]["$lte"] = user_preferences["precio_max"]
                
                if "precio_min" in user_preferences:
                    match_filter["precio_valor"]["$gte"] = user_preferences["precio_min"]
            
            pipeline = [
                {"$match": match_filter},
                {"$sort": {"precio_valor": 1}},  # Ordenar por precio ascendente
                {"$limit": limit},
                {
                    "$project": {
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
                        "fecha_extraccion": 1,
                        "ahorro_estimado": {
                            "$subtract": [
                                {"$avg": f"$precio_promedio_{categoria}"},
                                "$precio_valor"
                            ]
                        }
                    }
                }
            ]
            
            results = list(collection.aggregate(pipeline))
            
            # Convertir ObjectId a string
            for result in results:
                result["_id"] = str(result["_id"])
                
            return results
            
        except Exception as e:
            print(f"Error en get_best_prices_by_category: {e}")
            return _get_mock_best_prices(categoria, limit)
    
    @staticmethod
    def get_price_comparison(product_title: str) -> Dict[str, Any]:
        """
        Compara precios del mismo producto en diferentes tiendas
        
        Args:
            product_title: Título del producto a comparar
            
        Returns:
            Comparación de precios entre tiendas
        """
        if not MONGO_AVAILABLE or db is None:
            return _get_mock_price_comparison(product_title)
        
        try:
            collection = db["archivos"]
            
            # Búsqueda por similitud de título (usando regex)
            pipeline = [
                {
                    "$match": {
                        "titulo": {"$regex": product_title, "$options": "i"},
                        "precio_valor": {"$exists": True, "$ne": None}
                    }
                },
                {
                    "$group": {
                        "_id": "$fuente",
                        "precio_min": {"$min": "$precio_valor"},
                        "precio_max": {"$max": "$precio_valor"},
                        "precio_promedio": {"$avg": "$precio_valor"},
                        "count": {"$sum": 1},
                        "productos": {
                            "$push": {
                                "titulo": "$titulo",
                                "precio_valor": "$precio_valor",
                                "precio_texto": "$precio_texto",
                                "link": "$link",
                                "fecha_extraccion": "$fecha_extraccion"
                            }
                        }
                    }
                },
                {"$sort": {"precio_min": 1}}
            ]
            
            results = list(collection.aggregate(pipeline))
            
            if not results:
                return {"error": "No se encontraron productos similares"}
            
            # Calcular estadísticas generales
            all_prices = []
            for store in results:
                all_prices.extend([p["precio_valor"] for p in store["productos"]])
            
            return {
                "product_searched": product_title,
                "total_results": len(all_prices),
                "price_range": {
                    "min": min(all_prices),
                    "max": max(all_prices),
                    "average": sum(all_prices) / len(all_prices)
                },
                "stores": results,
                "best_deal": results[0] if results else None
            }
            
        except Exception as e:
            print(f"Error en get_price_comparison: {e}")
            return _get_mock_price_comparison(product_title)


def _get_mock_best_prices(categoria: str, limit: int) -> List[Dict[str, Any]]:
    """Datos mock para cuando MongoDB no está disponible"""
    return [
        {
            "_id": f"mock_id_{i}",
            "titulo": f"Producto {categoria} {i}",
            "marca": "NIKE" if i % 2 == 0 else "ADIDAS",
            "precio_texto": f"${100 - i * 5}",
            "precio_valor": 100 - i * 5,
            "moneda": "USD",
            "categoria": categoria,
            "imagen": f"https://example.com/image{i}.jpg",
            "link": f"https://example.com/product{i}",
            "fuente": "mock_store",
            "fecha_extraccion": "2025-09-24",
            "ahorro_estimado": i * 2
        }
        for i in range(1, min(limit + 1, 6))
    ]


def _get_mock_price_comparison(product_title: str) -> Dict[str, Any]:
    """Datos mock para comparación de precios"""
    return {
        "product_searched": product_title,
        "total_results": 3,
        "price_range": {
            "min": 85,
            "max": 120,
            "average": 102.5
        },
        "stores": [
            {
                "_id": "tienda_a",
                "precio_min": 85,
                "precio_max": 95,
                "precio_promedio": 90,
                "count": 2,
                "productos": [
                    {
                        "titulo": product_title,
                        "precio_valor": 85,
                        "precio_texto": "$85",
                        "link": "https://tienda-a.com/product",
                        "fecha_extraccion": "2025-09-24"
                    }
                ]
            },
            {
                "_id": "tienda_b", 
                "precio_min": 120,
                "precio_max": 120,
                "precio_promedio": 120,
                "count": 1,
                "productos": [
                    {
                        "titulo": product_title,
                        "precio_valor": 120,
                        "precio_texto": "$120",
                        "link": "https://tienda-b.com/product",
                        "fecha_extraccion": "2025-09-24"
                    }
                ]
            }
        ],
        "best_deal": {
            "_id": "tienda_a",
            "precio_min": 85,
            "count": 2
        }
    }