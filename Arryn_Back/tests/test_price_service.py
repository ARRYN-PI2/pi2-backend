from django.test import SimpleTestCase
from unittest.mock import MagicMock, patch
from bson import ObjectId

from Arryn_Back.domain.services import price_service
from Arryn_Back.tests.helpers.evidence_recorder import record_evidence


class PricePersonalizationServiceTests(SimpleTestCase):
    def test_get_best_prices_by_category_returns_mock_when_mongo_unavailable(self):
        with patch.object(price_service, "MONGO_AVAILABLE", False), patch.object(price_service, "db", None):
            results = price_service.PricePersonalizationService.get_best_prices_by_category(
                categoria="running", limit=3
            )

        self.assertGreater(len(results), 0)
        self.assertTrue(all(result["_id"].startswith("mock_id_") for result in results))
        record_evidence(self.id(), {
            "scenario": "mongo_unavailable",
            "categoria": "running",
            "limit": 3,
            "result_count": len(results),
            "sample": results[:2],
        })

    def test_get_best_prices_by_category_applies_user_preferences(self):
        mock_collection = MagicMock()
        fake_id = ObjectId()
        mock_collection.aggregate.return_value = [
            {
                "_id": fake_id,
                "titulo": "Zapatilla Running",
                "marca": "NIKE",
                "precio_valor": 120,
                "precio_texto": "$120",
            }
        ]

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection

        with patch.object(price_service, "MONGO_AVAILABLE", True), patch.object(price_service, "db", mock_db):
            results = price_service.PricePersonalizationService.get_best_prices_by_category(
                categoria="running",
                user_preferences={
                    "marcas_favoritas": ["NIKE"],
                    "precio_max": 150,
                    "precio_min": 100,
                },
                limit=5,
            )

        self.assertEqual(results[0]["_id"], str(fake_id))

        pipeline = mock_collection.aggregate.call_args[0][0]
        match_stage = pipeline[0]["$match"]
        self.assertEqual(match_stage["categoria"], "running")
        self.assertEqual(match_stage["marca"]["$in"], ["NIKE"])
        self.assertEqual(match_stage["precio_valor"]["$lte"], 150)
        self.assertEqual(match_stage["precio_valor"]["$gte"], 100)
        record_evidence(self.id(), {
            "categoria": "running",
            "user_preferences": {
                "marcas_favoritas": ["NIKE"],
                "precio_max": 150,
                "precio_min": 100,
            },
            "result": results,
            "match_filter": match_stage,
        })

    def test_get_price_comparison_builds_summary(self):
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value = [
            {
                "_id": "tienda_a",
                "precio_min": 80,
                "precio_max": 120,
                "precio_promedio": 95,
                "count": 2,
                "productos": [
                    {"precio_valor": 80},
                    {"precio_valor": 120},
                ],
            },
            {
                "_id": "tienda_b",
                "precio_min": 90,
                "precio_max": 130,
                "precio_promedio": 110,
                "count": 1,
                "productos": [
                    {"precio_valor": 130},
                ],
            },
        ]

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection

        with patch.object(price_service, "MONGO_AVAILABLE", True), patch.object(price_service, "db", mock_db):
            comparison = price_service.PricePersonalizationService.get_price_comparison("iPhone")

        self.assertEqual(comparison["product_searched"], "iPhone")
        self.assertEqual(comparison["price_range"]["min"], 80)
        self.assertEqual(comparison["price_range"]["max"], 130)
        self.assertEqual(comparison["total_results"], 3)
        self.assertEqual(comparison["best_deal"]["_id"], "tienda_a")
        record_evidence(self.id(), {
            "product": "iPhone",
            "price_range": comparison["price_range"],
            "total_results": comparison["total_results"],
            "best_deal": comparison["best_deal"],
        })
