"""
Servicio para generación de reportes básicos entre tiendas
"""
from typing import List, Dict, Any, Optional
from .mongo_service import db, MONGO_AVAILABLE
from datetime import datetime, timedelta
from collections import defaultdict
import math


class ReportService:
    """Servicio para generación de reportes y análisis de datos"""
    
    @staticmethod
    def generate_store_comparison_report(
        categoria: Optional[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Genera reporte de comparación entre tiendas
        
        Args:
            categoria: Filtrar por categoría específica
            days_back: Número de días hacia atrás para el análisis
            
        Returns:
            Reporte completo de comparación entre tiendas
        """
        if not MONGO_AVAILABLE or db is None:
            return _get_mock_store_report(categoria)
        
        try:
            collection = db["archivos"]
            start_date = datetime.now() - timedelta(days=days_back)
            
            # Filtro base
            match_filter = {
                "fecha_extraccion": {"$gte": start_date.strftime("%Y-%m-%d")},
                "precio_valor": {"$exists": True, "$ne": None}
            }
            if categoria:
                match_filter["categoria"] = categoria
            
            pipeline = [
                {"$match": match_filter},
                {
                    "$group": {
                        "_id": "$fuente",
                        "total_productos": {"$sum": 1},
                        "precio_promedio": {"$avg": "$precio_valor"},
                        "precio_min": {"$min": "$precio_valor"},
                        "precio_max": {"$max": "$precio_valor"},
                        "categorias": {"$addToSet": "$categoria"},
                        "marcas": {"$addToSet": "$marca"},
                        "ultima_actualizacion": {"$max": "$fecha_extraccion"}
                    }
                },
                {
                    "$addFields": {
                        "total_categorias": {"$size": "$categorias"},
                        "total_marcas": {"$size": "$marcas"},
                        "rango_precios": {"$subtract": ["$precio_max", "$precio_min"]}
                    }
                },
                {"$sort": {"total_productos": -1}}
            ]
            
            stores_data = list(collection.aggregate(pipeline))
            
            # Calcular estadísticas generales
            total_productos = sum(store["total_productos"] for store in stores_data)
            total_tiendas = len(stores_data)
            
            # Calcular mejor tienda por diferentes métricas
            mejor_por_precio = min(stores_data, key=lambda x: x["precio_promedio"]) if stores_data else None
            mejor_por_variedad = max(stores_data, key=lambda x: x["total_productos"]) if stores_data else None
            
            return {
                "periodo_analisis": {
                    "fecha_inicio": start_date.strftime("%Y-%m-%d"),
                    "fecha_fin": datetime.now().strftime("%Y-%m-%d"),
                    "dias_analizados": days_back
                },
                "resumen_general": {
                    "total_tiendas": total_tiendas,
                    "total_productos": total_productos,
                    "categoria_filtro": categoria,
                    "promedio_productos_por_tienda": round(total_productos / total_tiendas, 2) if total_tiendas > 0 else 0
                },
                "rankings": {
                    "mejor_precio_promedio": mejor_por_precio,
                    "mayor_variedad": mejor_por_variedad,
                    "mas_actualizada": max(stores_data, key=lambda x: x["ultima_actualizacion"]) if stores_data else None
                },
                "detalle_tiendas": stores_data,
                "generado_en": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error en generate_store_comparison_report: {e}")
            return _get_mock_store_report(categoria)
    
    @staticmethod
    def generate_price_analysis_report(categoria: str, days_back: int = 30) -> Dict[str, Any]:
        """
        Genera análisis de precios por categoría
        
        Args:
            categoria: Categoría a analizar
            days_back: Días hacia atrás para el análisis
            
        Returns:
            Reporte de análisis de precios
        """
        if not MONGO_AVAILABLE or db is None:
            return _get_mock_price_analysis(categoria)
        
        try:
            collection = db["archivos"]
            start_date = datetime.now() - timedelta(days=days_back)
            
            pipeline = [
                {
                    "$match": {
                        "categoria": categoria,
                        "fecha_extraccion": {"$gte": start_date.strftime("%Y-%m-%d")},
                        "precio_valor": {"$exists": True, "$ne": None}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "precio_promedio": {"$avg": "$precio_valor"},
                        "precio_min": {"$min": "$precio_valor"},
                        "precio_max": {"$max": "$precio_valor"},
                        "total_productos": {"$sum": 1},
                        "precios": {"$push": "$precio_valor"}
                    }
                },
                {
                    "$addFields": {
                        "rango_precios": {"$subtract": ["$precio_max", "$precio_min"]},
                        "precios_ordenados": {"$sortArray": {"input": "$precios", "sortBy": 1}}
                    }
                }
            ]
            
            result = list(collection.aggregate(pipeline))
            
            if not result:
                return {"error": f"No se encontraron datos para la categoría {categoria}"}
            
            data = result[0]
            precios = data["precios_ordenados"]
            
            # Calcular percentiles
            def get_percentile(prices, percentile):
                if not prices:
                    return 0
                k = (len(prices) - 1) * percentile / 100
                f = math.floor(k)
                c = math.ceil(k)
                if f == c:
                    return prices[int(k)]
                return prices[int(f)] * (c - k) + prices[int(c)] * (k - f)
            
            # Análisis por rangos de precio
            ranges = {
                "economico": len([p for p in precios if p <= get_percentile(precios, 33)]),
                "medio": len([p for p in precios if get_percentile(precios, 33) < p <= get_percentile(precios, 66)]),
                "premium": len([p for p in precios if p > get_percentile(precios, 66)])
            }
            
            return {
                "categoria": categoria,
                "periodo_analisis": {
                    "fecha_inicio": start_date.strftime("%Y-%m-%d"),
                    "fecha_fin": datetime.now().strftime("%Y-%m-%d"),
                    "dias_analizados": days_back
                },
                "estadisticas_generales": {
                    "total_productos": data["total_productos"],
                    "precio_promedio": round(data["precio_promedio"], 2),
                    "precio_minimo": data["precio_min"],
                    "precio_maximo": data["precio_max"],
                    "rango_precios": round(data["rango_precios"], 2)
                },
                "percentiles": {
                    "p25": round(get_percentile(precios, 25), 2),
                    "p50_mediana": round(get_percentile(precios, 50), 2),
                    "p75": round(get_percentile(precios, 75), 2),
                    "p90": round(get_percentile(precios, 90), 2)
                },
                "distribucion_rangos": ranges,
                "recomendaciones": {
                    "precio_competitivo": round(get_percentile(precios, 25), 2),
                    "precio_premium_aceptable": round(get_percentile(precios, 75), 2),
                    "oportunidad_descuento": round(data["precio_promedio"] * 0.8, 2)
                },
                "generado_en": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error en generate_price_analysis_report: {e}")
            return _get_mock_price_analysis(categoria)


def _get_mock_store_report(categoria: Optional[str]) -> Dict[str, Any]:
    """Reporte mock para cuando MongoDB no está disponible"""
    return {
        "periodo_analisis": {
            "fecha_inicio": "2025-08-25",
            "fecha_fin": "2025-09-24",
            "dias_analizados": 30
        },
        "resumen_general": {
            "total_tiendas": 3,
            "total_productos": 150,
            "categoria_filtro": categoria,
            "promedio_productos_por_tienda": 50
        },
        "rankings": {
            "mejor_precio_promedio": {
                "_id": "tienda_economica",
                "precio_promedio": 85.5,
                "total_productos": 45
            },
            "mayor_variedad": {
                "_id": "mega_tienda",
                "total_productos": 75,
                "precio_promedio": 120.0
            }
        },
        "detalle_tiendas": [
            {
                "_id": "tienda_economica",
                "total_productos": 45,
                "precio_promedio": 85.5,
                "precio_min": 20,
                "precio_max": 200,
                "total_categorias": 8,
                "total_marcas": 15
            },
            {
                "_id": "mega_tienda", 
                "total_productos": 75,
                "precio_promedio": 120.0,
                "precio_min": 30,
                "precio_max": 500,
                "total_categorias": 12,
                "total_marcas": 25
            }
        ],
        "generado_en": datetime.now().isoformat()
    }


def _get_mock_price_analysis(categoria: str) -> Dict[str, Any]:
    """Análisis de precios mock"""
    return {
        "categoria": categoria,
        "periodo_analisis": {
            "fecha_inicio": "2025-08-25",
            "fecha_fin": "2025-09-24",
            "dias_analizados": 30
        },
        "estadisticas_generales": {
            "total_productos": 50,
            "precio_promedio": 125.50,
            "precio_minimo": 25.99,
            "precio_maximo": 299.99,
            "rango_precios": 274.0
        },
        "percentiles": {
            "p25": 75.0,
            "p50_mediana": 115.0,
            "p75": 175.0,
            "p90": 225.0
        },
        "distribucion_rangos": {
            "economico": 17,
            "medio": 20,
            "premium": 13
        },
        "recomendaciones": {
            "precio_competitivo": 75.0,
            "precio_premium_aceptable": 175.0,
            "oportunidad_descuento": 100.4
        },
        "generado_en": datetime.now().isoformat()
    }