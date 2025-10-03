import json
import time
from unittest.mock import MagicMock, patch

from django.http import JsonResponse
from django.test import SimpleTestCase, override_settings
from django.core.cache import cache

from Arryn_Back.infrastructure.middleware import performance
from Arryn_Back.tests.helpers.evidence_recorder import record_evidence


class RateLimitMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.get_response = MagicMock(return_value=JsonResponse({"ok": True}))
        self.middleware = performance.RateLimitMiddleware(self.get_response)
        self.middleware.rate_limit = 2
        self.middleware.window_size = 60

    @override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
    def test_allows_requests_within_limit(self):
        cache.clear()
        request = MagicMock()
        request.META = {"REMOTE_ADDR": "127.0.0.1"}

        response = self.middleware.process_request(request)

        self.assertIsNone(response)
        record_evidence(self.id(), {
            "ip": "127.0.0.1",
            "within_limit": True,
            "cache_entry": cache.get("rate_limit_127.0.0.1"),
        })

    @override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
    def test_blocks_when_limit_exceeded(self):
        cache.clear()
        request = MagicMock()
        request.META = {"REMOTE_ADDR": "127.0.0.1"}

        cache_key = "rate_limit_127.0.0.1"
        cache.set(
            cache_key,
            {"count": self.middleware.rate_limit, "window_start": time.time()},
            self.middleware.window_size,
        )

        response = self.middleware.process_request(request)

        self.assertIsNotNone(response)
        self.assertIsInstance(response, JsonResponse)
        assert response is not None
        self.assertEqual(response.status_code, 429)
        record_evidence(self.id(), {
            "ip": "127.0.0.1",
            "response": json.loads(response.content.decode()),
            "cache_entry": cache.get(cache_key),
        })


class ResponseCacheMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.get_response = MagicMock(return_value=JsonResponse({"data": 42}))
        self.middleware = performance.ResponseCacheMiddleware(self.get_response)
        self.middleware.cache_timeout = 10

    @override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
    def test_returns_cached_response(self):
        request = MagicMock()
        request.method = "GET"
        request.path = "/api/best-prices/"
        request.get_full_path.return_value = "/api/best-prices/?limit=5"

        cached_payload = {"cached": True}

        with patch.object(self.middleware, "generate_cache_key", return_value="cache-key"):
            cache.clear()
            cache.set("cache-key", cached_payload, self.middleware.cache_timeout)
            response = self.middleware.process_request(request)

        self.assertIsNotNone(response)
        self.assertIsInstance(response, JsonResponse)
        assert response is not None
        self.assertEqual(json.loads(response.content.decode()), cached_payload)
        record_evidence(self.id(), {
            "path": request.path,
            "cache_key": "cache-key",
            "returned_payload": json.loads(response.content.decode()),
        })

    @override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
    def test_caches_successful_response(self):
        request = MagicMock()
        request.method = "GET"
        request.path = "/api/best-prices/"
        request.get_full_path.return_value = "/api/best-prices/?limit=5"

        with patch.object(self.middleware, "generate_cache_key", return_value="cache-key"):
            response = self.middleware.process_response(request, JsonResponse({"data": 42}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(cache.get("cache-key"), {"data": 42})
        record_evidence(self.id(), {
            "path": request.path,
            "cache_key": "cache-key",
            "cached_value": cache.get("cache-key"),
        })


class RequestLoggingMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.get_response = MagicMock(return_value=JsonResponse({"ok": True}))
        self.middleware = performance.RequestLoggingMiddleware(self.get_response)

    @patch("Arryn_Back.infrastructure.middleware.performance.logger")
    def test_logs_slow_requests(self, logger_mock):
        request = MagicMock()
        request.method = "GET"
        request.path = "/api/test/"
        request.start_time = time.time() - 2

        response = JsonResponse({"ok": True})

        with patch("os.getenv", return_value="1.0"):
            self.middleware.process_response(request, response)

        logger_mock.warning.assert_called()
        record_evidence(self.id(), {
            "path": request.path,
            "duration_seconds": 2,
            "logged_message": logger_mock.warning.call_args[0][0],
        })

    @patch("Arryn_Back.infrastructure.middleware.performance.logger")
    def test_logs_fast_requests(self, logger_mock):
        request = MagicMock()
        request.method = "GET"
        request.path = "/api/test/"
        request.start_time = time.time() - 0.1

        response = JsonResponse({"ok": True})

        with patch("os.getenv", return_value="1.0"):
            self.middleware.process_response(request, response)

        logger_mock.info.assert_called()
        record_evidence(self.id(), {
            "path": request.path,
            "duration_seconds": 0.1,
            "logged_message": logger_mock.info.call_args[0][0],
        })
