from django.test import SimpleTestCase
from unittest.mock import MagicMock, patch
from bson import ObjectId

from Arryn_Back.domain.services import ranking_service
from Arryn_Back.tests.helpers.evidence_recorder import record_evidence


class OfferRankingServiceTests(SimpleTestCase):
    def test_rank_offers_by_value_returns_mock_when_mongo_unavailable(self):
        with patch.object(ranking_service, "MONGO_AVAILABLE", False), patch.object(ranking_service, "db", None):
            results = ranking_service.OfferRankingService.rank_offers_by_value(limit=3)

        self.assertGreater(len(results), 0)
        self.assertTrue(all(result["_id"].startswith("mock_ranked_") for result in results))
        record_evidence(self.id(), {
            "scenario": "mongo_unavailable",
            "limit": 3,
            "result_count": len(results),
            "sample": results[:2],
        })

    def test_rank_offers_by_value_formats_scores(self):
        mock_collection = MagicMock()
        fake_id = ObjectId()
        mock_collection.aggregate.return_value = [
            {
                "_id": fake_id,
                "titulo": "Oferta smart TV",
                "score_total": 0.95781,
                "score_precio": 0.81234,
                "score_freshness": 0.91234,
                "ahorro_vs_promedio": 15.6789,
                "percentil_precio": 24.987,
            }
        ]

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection

        with patch.object(ranking_service, "MONGO_AVAILABLE", True), patch.object(ranking_service, "db", mock_db):
            results = ranking_service.OfferRankingService.rank_offers_by_value(limit=1)

        self.assertEqual(results[0]["_id"], str(fake_id))
        self.assertEqual(results[0]["score_total"], 0.958)
        self.assertEqual(results[0]["score_precio"], 0.812)
        self.assertEqual(results[0]["score_freshness"], 0.912)
        self.assertEqual(results[0]["ahorro_vs_promedio"], 15.68)
        self.assertEqual(results[0]["percentil_precio"], 25.0)
        record_evidence(self.id(), {
            "result": results[0],
            "raw_scores": {
                "score_total": 0.95781,
                "score_precio": 0.81234,
                "score_freshness": 0.91234,
                "ahorro_vs_promedio": 15.6789,
                "percentil_precio": 24.987,
            },
        })

    def test_get_trending_offers_rounds_scores(self):
        mock_collection = MagicMock()
        fake_id = ObjectId()
        mock_collection.aggregate.return_value = [
            {
                "_id": fake_id,
                "trending_score": 98.7654,
                "precio_promedio_encontrado": 250.6789,
            }
        ]

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection

        with patch.object(ranking_service, "MONGO_AVAILABLE", True), patch.object(ranking_service, "db", mock_db):
            results = ranking_service.OfferRankingService.get_trending_offers(limit=1)

        self.assertEqual(results[0]["_id"], str(fake_id))
        self.assertEqual(results[0]["trending_score"], 98.77)
        self.assertEqual(results[0]["precio_promedio_encontrado"], 250.68)
        record_evidence(self.id(), {
            "result": results[0],
            "raw_values": {
                "trending_score": 98.7654,
                "precio_promedio_encontrado": 250.6789,
            },
        })
