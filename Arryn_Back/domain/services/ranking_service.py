"""
Servicio para ranking de ofertas por valor y algoritmos de recomendación
"""
from typing import List, Dict, Any, Optional
from .mongo_service import db, MONGO_AVAILABLE
from datetime import datetime, timedelta
import math


class OfferRankingService:
    """Servicio para ranking y valoración de ofertas"""
    
    @staticmethod
    def rank_offers_by_value(
        categoria: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Rankea ofertas por valor usando algoritmo personalizado
        
        Args:
            categoria: Filtrar por categoría específica
            user_id: ID del usuario para personalización
            limit: Número máximo de resultados
            
        Returns:
            Lista de ofertas rankeadas por valor
        """
        if not MONGO_AVAILABLE or db is None:
            return _get_mock_ranked_offers(categoria, limit)
        
        try:
            collection = db["archivos"]
            
            # Filtro base
            match_filter = {"precio_valor": {"$exists": True, "$ne": None}}
            if categoria:
                match_filter["categoria"] = {"$eq": categoria}
            
            pipeline = [
                {"$match": match_filter},
                {
                    "$addFields": {
                        "dias_desde_extraccion": {
                            "$divide": [
                                {"$subtract": [datetime.now(), {"$dateFromString": {"dateString": "$fecha_extraccion"}}]},
                                86400000  # milisegundos en un día
                            ]
                        }
                    }
                },
                {
                    "$addFields": {
                        "score_freshness": {
                            "$cond": {
                                "if": {"$lte": ["$dias_desde_extraccion", 1]},
                                "then": 1.0,
                                "else": {
                                    "$divide": [
                                        1,
                                        {"$add": [1, {"$multiply": ["$dias_desde_extraccion", 0.1]}]}
                                    ]
                                }
                            }
                        }
                    }
                },
                {
                    "$lookup": {
                        "from": "archivos",
                        "let": {"current_categoria": "$categoria"},
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$categoria", "$$current_categoria"]}}},
                            {"$group": {
                                "_id": None,
                                "precio_promedio": {"$avg": "$precio_valor"},
                                "precio_min": {"$min": "$precio_valor"},
                                "precio_max": {"$max": "$precio_valor"}
                            }}
                        ],
                        "as": "categoria_stats"
                    }
                },
                {
                    "$addFields": {
                        "categoria_stats": {"$arrayElemAt": ["$categoria_stats", 0]}
                    }
                },
                {
                    "$addFields": {
                        "score_precio": {
                            "$cond": {
                                "if": {"$gt": ["$categoria_stats.precio_max", "$categoria_stats.precio_min"]},
                                "then": {
                                    "$divide": [
                                        {"$subtract": ["$categoria_stats.precio_max", "$precio_valor"]},
                                        {"$subtract": ["$categoria_stats.precio_max", "$categoria_stats.precio_min"]}
                                    ]
                                },
                                "else": 0.5
                            }
                        }
                    }
                },
                {
                    "$addFields": {
                        "score_total": {
                            "$add": [
                                {"$multiply": ["$score_precio", 0.6]},      # 60% peso al precio
                                {"$multiply": ["$score_freshness", 0.4]}    # 40% peso a la frescura
                            ]
                        }
                    }
                },
                {"$sort": {"score_total": -1}},
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
                        "score_total": 1,
                        "score_precio": 1,
                        "score_freshness": 1,
                        "ahorro_vs_promedio": {
                            "$subtract": ["$categoria_stats.precio_promedio", "$precio_valor"]
                        },
                        "percentil_precio": {
                            "$multiply": [{"$subtract": [1, "$score_precio"]}, 100]
                        }
                    }
                }
            ]
            
            results = list(collection.aggregate(pipeline))
            
            # Convertir ObjectId a string y limpiar datos
            for result in results:
                result["_id"] = str(result["_id"])
                result["score_total"] = round(result.get("score_total", 0), 3)
                result["score_precio"] = round(result.get("score_precio", 0), 3)
                result["score_freshness"] = round(result.get("score_freshness", 0), 3)
                result["ahorro_vs_promedio"] = round(result.get("ahorro_vs_promedio", 0), 2)
                result["percentil_precio"] = round(result.get("percentil_precio", 0), 1)
                
            return results
            
        except Exception as e:
            print(f"Error en rank_offers_by_value: {e}")
            return _get_mock_ranked_offers(categoria, limit)
    
    @staticmethod
    def get_trending_offers(timeframe_days: int = 7, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Obtiene ofertas que están en tendencia (muchas vistas, buenos precios, recientes)
        
        Args:
            timeframe_days: Ventana de tiempo en días para considerar "trending"
            limit: Número máximo de resultados
            
        Returns:
            Lista de ofertas trending
        """
        if not MONGO_AVAILABLE or db is None:
            return _get_mock_trending_offers(limit)
        
        try:
            collection = db["archivos"]
            start_date = datetime.now() - timedelta(days=timeframe_days)
            
            pipeline = [
                {
                    "$match": {
                        "fecha_extraccion": {"$gte": start_date.strftime("%Y-%m-%d")},
                        "precio_valor": {"$exists": True, "$ne": None}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "titulo_normalizado": {"$toLower": "$titulo"},
                            "marca": "$marca"
                        },
                        "count": {"$sum": 1},
                        "precio_min": {"$min": "$precio_valor"},
                        "precio_promedio": {"$avg": "$precio_valor"},
                        "fuentes": {"$addToSet": "$fuente"},
                        "ultimo_documento": {"$last": "$$ROOT"}
                    }
                },
                {
                    "$addFields": {
                        "score_trending": {
                            "$add": [
                                {"$multiply": ["$count", 0.4]},          # 40% por frecuencia
                                {"$multiply": [{"$size": "$fuentes"}, 0.3]}, # 30% por múltiples fuentes
                                {"$divide": [1000, "$precio_min"]}       # 30% inversamente proporcional al precio
                            ]
                        }
                    }
                },
                {"$sort": {"score_trending": -1}},
                {"$limit": limit},
                {
                    "$replaceRoot": {
                        "newRoot": {
                            "$mergeObjects": [
                                "$ultimo_documento",
                                {
                                    "trending_score": "$score_trending",
                                    "apariciones": "$count",
                                    "fuentes_count": {"$size": "$fuentes"},
                                    "precio_min_encontrado": "$precio_min",
                                    "precio_promedio_encontrado": "$precio_promedio"
                                }
                            ]
                        }
                    }
                }
            ]
            
            results = list(collection.aggregate(pipeline))
            
            # Limpiar datos
            for result in results:
                result["_id"] = str(result["_id"])
                result["trending_score"] = round(result.get("trending_score", 0), 2)
                result["precio_promedio_encontrado"] = round(result.get("precio_promedio_encontrado", 0), 2)
                
            return results
            
        except Exception as e:
            print(f"Error en get_trending_offers: {e}")
            return _get_mock_trending_offers(limit)


def _get_mock_ranked_offers(categoria: Optional[str], limit: int) -> List[Dict[str, Any]]:
    """Datos mock para ofertas rankeadas"""
    base_categoria = categoria or "electronics"
    return [
        {
            "_id": f"mock_ranked_{i}",
            "titulo": f"Top Oferta {base_categoria} #{i}",
            "marca": ["NIKE", "ADIDAS", "APPLE", "SAMSUNG"][i % 4],
            "precio_texto": f"${150 - i * 10}",
            "precio_valor": 150 - i * 10,
            "moneda": "USD",
            "categoria": base_categoria,
            "imagen": f"https://example.com/ranked{i}.jpg",
            "link": f"https://example.com/ranked{i}",
            "fuente": "mock_store",
            "fecha_extraccion": "2025-09-24",
            "score_total": round(0.95 - i * 0.1, 3),
            "score_precio": round(0.9 - i * 0.08, 3),
            "score_freshness": 1.0,
            "ahorro_vs_promedio": (20 - i * 2),
            "percentil_precio": round(10 + i * 5, 1)
        }
        for i in range(min(limit, 10))
    ]


def _get_mock_trending_offers(limit: int) -> List[Dict[str, Any]]:
    """Datos mock para ofertas trending"""
    productos_trending = [
        "iPhone 15 Pro", "MacBook Air M3", "AirPods Pro", "Nike Air Max", 
        "Samsung Galaxy S24", "PlayStation 5", "Nintendo Switch", "iPad Pro"
    ]
    
    return [
        {
            "_id": f"mock_trending_{i}",
            "titulo": productos_trending[i % len(productos_trending)],
            "marca": ["APPLE", "NIKE", "SAMSUNG", "SONY"][i % 4],
            "precio_texto": f"${200 + i * 50}",
            "precio_valor": 200 + i * 50,
            "moneda": "USD", 
            "categoria": "trending",
            "imagen": f"https://example.com/trending{i}.jpg",
            "link": f"https://example.com/trending{i}",
            "fuente": "trending_store",
            "fecha_extraccion": "2025-09-24",
            "trending_score": round(100 - i * 5, 2),
            "apariciones": 10 - i,
            "fuentes_count": 3 if i < 3 else 2,
            "precio_min_encontrado": 200 + i * 50 - 20,
            "precio_promedio_encontrado": 200 + i * 50 + 10
        }
        for i in range(min(limit, 8))
    ]