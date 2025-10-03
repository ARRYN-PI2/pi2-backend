from django.test import SimpleTestCase
from unittest.mock import MagicMock, patch

from Arryn_Back.domain.services import report_service
from Arryn_Back.tests.helpers.evidence_recorder import record_evidence


class ReportServiceTests(SimpleTestCase):
    def test_generate_store_comparison_report_aggregates_data(self):
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value = [
            {
                "_id": "store_a",
                "total_productos": 10,
                "precio_promedio": 90.5,
                "precio_min": 50,
                "precio_max": 120,
                "categorias": ["electronics"],
                "marcas": ["NIKE"],
                "ultima_actualizacion": "2025-09-20",
                "total_categorias": 1,
                "total_marcas": 1,
                "rango_precios": 70,
            },
            {
                "_id": "store_b",
                "total_productos": 20,
                "precio_promedio": 150.0,
                "precio_min": 80,
                "precio_max": 220,
                "categorias": ["electronics", "fitness"],
                "marcas": ["ADIDAS", "PUMA"],
                "ultima_actualizacion": "2025-09-21",
                "total_categorias": 2,
                "total_marcas": 2,
                "rango_precios": 140,
            },
        ]

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection

        with patch.object(report_service, "MONGO_AVAILABLE", True), patch.object(report_service, "db", mock_db):
            report = report_service.ReportService.generate_store_comparison_report(days_back=15)

        resumen = report["resumen_general"]
        self.assertEqual(resumen["total_tiendas"], 2)
        self.assertEqual(resumen["total_productos"], 30)
        self.assertEqual(resumen["promedio_productos_por_tienda"], 15.0)
        self.assertEqual(report["rankings"]["mejor_precio_promedio"]["_id"], "store_a")
        self.assertEqual(report["rankings"]["mayor_variedad"]["_id"], "store_b")
        self.assertEqual(len(report["detalle_tiendas"]), 2)
        record_evidence(self.id(), {
            "days_back": 15,
            "summary": resumen,
            "rankings": report["rankings"],
            "stores": report["detalle_tiendas"],
        })

    def test_generate_store_comparison_report_returns_mock_when_mongo_unavailable(self):
        with patch.object(report_service, "MONGO_AVAILABLE", False), patch.object(report_service, "db", None):
            report = report_service.ReportService.generate_store_comparison_report(categoria="electronics")

        self.assertIn("resumen_general", report)
        self.assertEqual(report["resumen_general"]["categoria_filtro"], "electronics")
        record_evidence(self.id(), {
            "categoria": "electronics",
            "resumen": report["resumen_general"],
        })

    def test_generate_price_analysis_report_computes_percentiles(self):
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value = [
            {
                "precio_promedio": 75.0,
                "precio_min": 50,
                "precio_max": 110,
                "total_productos": 4,
                "precios": [50, 70, 90, 110],
                "rango_precios": 60,
                "precios_ordenados": [50, 70, 90, 110],
            }
        ]

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection

        with patch.object(report_service, "MONGO_AVAILABLE", True), patch.object(report_service, "db", mock_db):
            report = report_service.ReportService.generate_price_analysis_report(categoria="electronics")

        self.assertEqual(report["estadisticas_generales"]["precio_promedio"], 75.0)
        self.assertEqual(report["percentiles"]["p50_mediana"], 80.0)
        self.assertEqual(sum(report["distribucion_rangos"].values()), 4)
        record_evidence(self.id(), {
            "categoria": "electronics",
            "estadisticas_generales": report["estadisticas_generales"],
            "percentiles": report["percentiles"],
            "distribucion_rangos": report["distribucion_rangos"],
        })

    def test_generate_price_analysis_report_returns_error_when_no_data(self):
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value = []

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection

        with patch.object(report_service, "MONGO_AVAILABLE", True), patch.object(report_service, "db", mock_db):
            report = report_service.ReportService.generate_price_analysis_report(categoria="unknown")

        self.assertEqual(report["error"], "No se encontraron datos para la categoría unknown")
        record_evidence(self.id(), {
            "categoria": "unknown",
            "error": report["error"],
        })
