"""
Tests for the Koko Finance Python SDK.

Uses unittest.mock to mock HTTP calls — no real API key or server needed.
"""

import json
import unittest
from unittest.mock import patch, MagicMock

from koko_finance import (
    KokoClient,
    KokoError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    ServerError,
)


def _mock_response(status_code=200, json_data=None, headers=None):
    """Create a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.json.return_value = json_data or {}
    resp.text = json.dumps(json_data) if json_data else ""
    return resp


def _api_response(data, success=True, error=None):
    """Build a standard APIResponse envelope."""
    return {
        "success": success,
        "data": data,
        "metadata": {
            "request_id": "abc123",
            "api_version": "v1",
            "latency_ms": 150,
            "timestamp": "2026-03-04T14:30:00.000Z",
        },
        "error": error,
    }


class TestKokoClientInit(unittest.TestCase):
    def test_requires_api_key(self):
        with self.assertRaises(ValueError):
            KokoClient(api_key="")

    def test_default_base_url(self):
        client = KokoClient(api_key="koko_test123")
        self.assertEqual(client._base_url, "https://kokofinance.net")

    def test_custom_base_url(self):
        client = KokoClient(api_key="koko_test123", base_url="http://localhost:8000/")
        self.assertEqual(client._base_url, "http://localhost:8000")

    def test_headers_set(self):
        client = KokoClient(api_key="koko_test123")
        self.assertEqual(client._session.headers["X-API-Key"], "koko_test123")


class TestAnalyzePortfolio(unittest.TestCase):
    @patch("koko_finance.client.requests.Session.request")
    def test_basic_call(self, mock_request):
        mock_request.return_value = _mock_response(
            200,
            _api_response({"portfolio_summary": {"total_value": 500}}),
        )
        client = KokoClient(api_key="koko_test123")
        result = client.analyze_portfolio(
            cards=[
                {"card_name": "Chase Sapphire Preferred", "annual_fee": 95},
                {"card_name": "American Express Gold Card", "annual_fee": 250},
            ],
            spending={"dining": 500, "travel": 300},
            primary_goal="travel",
        )
        self.assertEqual(result["portfolio_summary"]["total_value"], 500)

        # Verify request payload
        call_args = mock_request.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        self.assertEqual(len(payload["cards"]), 2)
        self.assertEqual(payload["params"]["spending"]["dining"], 500)
        self.assertEqual(payload["params"]["primary_goal"], "travel")

    @patch("koko_finance.client.requests.Session.request")
    def test_no_params(self, mock_request):
        mock_request.return_value = _mock_response(
            200, _api_response({"portfolio_summary": {}})
        )
        client = KokoClient(api_key="koko_test123")
        result = client.analyze_portfolio(
            cards=[{"card_name": "Citi Double Cash"}]
        )
        call_args = mock_request.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        self.assertNotIn("params", payload)


class TestCompareCards(unittest.TestCase):
    @patch("koko_finance.client.requests.Session.request")
    def test_basic_call(self, mock_request):
        mock_request.return_value = _mock_response(
            200,
            _api_response({"winner": "Chase Sapphire Preferred"}),
        )
        client = KokoClient(api_key="koko_test123")
        result = client.compare_cards(
            cards=[
                {"card_name": "Chase Sapphire Preferred", "annual_fee": 95},
                {"card_name": "Capital One Venture X", "annual_fee": 395},
            ],
            spending={"dining": 400, "travel": 500},
            primary_goal="travel",
        )
        self.assertEqual(result["winner"], "Chase Sapphire Preferred")

        # Verify card_names extracted correctly
        call_args = mock_request.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        self.assertEqual(
            payload["card_names"],
            ["Chase Sapphire Preferred", "Capital One Venture X"],
        )


class TestRecommendCard(unittest.TestCase):
    @patch("koko_finance.client.requests.Session.request")
    def test_market_mode(self, mock_request):
        mock_request.return_value = _mock_response(
            200,
            _api_response({"recommendations": [{"card_name": "AmEx Gold"}]}),
        )
        client = KokoClient(api_key="koko_test123")
        result = client.recommend_card(
            category="dining",
            spending={"dining": 600},
            credit_tier="excellent",
        )
        self.assertEqual(result["recommendations"][0]["card_name"], "AmEx Gold")

    @patch("koko_finance.client.requests.Session.request")
    def test_portfolio_mode(self, mock_request):
        mock_request.return_value = _mock_response(
            200,
            _api_response({"recommended_card": {"card_name": "Chase Sapphire Preferred"}}),
        )
        client = KokoClient(api_key="koko_test123")
        result = client.recommend_card(
            category="dining",
            portfolio_card_names=["Chase Sapphire Preferred", "Citi Double Cash"],
        )
        self.assertIn("recommended_card", result)

        call_args = mock_request.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        self.assertEqual(len(payload["portfolio_card_names"]), 2)


class TestCheckRenewal(unittest.TestCase):
    @patch("koko_finance.client.requests.Session.request")
    def test_basic_call(self, mock_request):
        mock_request.return_value = _mock_response(
            200,
            _api_response({"verdict": "RENEW", "year2_net_value": 120}),
        )
        client = KokoClient(api_key="koko_test123")
        result = client.check_renewal(
            card={"card_name": "Chase Sapphire Preferred", "annual_fee": 95},
            spending={"dining": 400, "travel": 300},
        )
        self.assertEqual(result["verdict"], "RENEW")
        self.assertEqual(result["year2_net_value"], 120)


class TestHealth(unittest.TestCase):
    @patch("koko_finance.client.requests.Session.request")
    def test_health(self, mock_request):
        mock_request.return_value = _mock_response(
            200,
            {"status": "healthy", "checks": {"api": "ok"}},
        )
        client = KokoClient(api_key="koko_test123")
        result = client.health()
        self.assertEqual(result["status"], "healthy")


class TestErrorHandling(unittest.TestCase):
    @patch("koko_finance.client.requests.Session.request")
    def test_401_raises_authentication_error(self, mock_request):
        mock_request.return_value = _mock_response(
            401,
            {"detail": {"error": "invalid_api_key", "message": "Invalid API key"}},
        )
        client = KokoClient(api_key="koko_bad_key")
        with self.assertRaises(AuthenticationError) as ctx:
            client.health()
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("Invalid API key", ctx.exception.message)

    @patch("koko_finance.client.requests.Session.request")
    def test_429_raises_rate_limit_error(self, mock_request):
        mock_request.return_value = _mock_response(
            429,
            {"detail": {"error": "rate_limit_exceeded", "message": "Rate limit: 60 requests/minute"}},
            headers={"Retry-After": "30"},
        )
        client = KokoClient(api_key="koko_test123")
        with self.assertRaises(RateLimitError) as ctx:
            client.analyze_portfolio(cards=[{"card_name": "Test Card"}])
        self.assertEqual(ctx.exception.status_code, 429)
        self.assertEqual(ctx.exception.retry_after, 30)

    @patch("koko_finance.client.requests.Session.request")
    def test_422_raises_validation_error(self, mock_request):
        mock_request.return_value = _mock_response(
            422,
            {"detail": [{"loc": ["body", "cards"], "msg": "field required", "type": "value_error.missing"}]},
        )
        client = KokoClient(api_key="koko_test123")
        with self.assertRaises(ValidationError) as ctx:
            client.analyze_portfolio(cards=[])
        self.assertEqual(ctx.exception.status_code, 422)

    @patch("koko_finance.client.requests.Session.request")
    def test_500_raises_server_error(self, mock_request):
        mock_request.return_value = _mock_response(
            500,
            {"detail": {"message": "Internal server error"}},
        )
        client = KokoClient(api_key="koko_test123")
        with self.assertRaises(ServerError) as ctx:
            client.health()
        self.assertEqual(ctx.exception.status_code, 500)

    @patch("koko_finance.client.requests.Session.request")
    def test_connection_error(self, mock_request):
        mock_request.side_effect = __import__("requests").ConnectionError("Connection refused")
        client = KokoClient(api_key="koko_test123")
        with self.assertRaises(KokoError) as ctx:
            client.health()
        self.assertIn("Connection error", ctx.exception.message)

    @patch("koko_finance.client.requests.Session.request")
    def test_timeout_error(self, mock_request):
        mock_request.side_effect = __import__("requests").Timeout("Timeout")
        client = KokoClient(api_key="koko_test123", timeout=5)
        with self.assertRaises(KokoError) as ctx:
            client.health()
        self.assertIn("timed out", ctx.exception.message)


class TestEnvelopeUnwrapping(unittest.TestCase):
    @patch("koko_finance.client.requests.Session.request")
    def test_returns_data_field(self, mock_request):
        """Verify the client unwraps the APIResponse envelope and returns .data"""
        mock_request.return_value = _mock_response(
            200,
            {
                "success": True,
                "data": {"portfolio_summary": {"total_value": 500}},
                "metadata": {"request_id": "abc123"},
                "error": None,
            },
        )
        client = KokoClient(api_key="koko_test123")
        result = client.analyze_portfolio(
            cards=[{"card_name": "Test Card"}]
        )
        # Should get the inner data, not the envelope
        self.assertIn("portfolio_summary", result)
        self.assertNotIn("success", result)
        self.assertNotIn("metadata", result)


if __name__ == "__main__":
    unittest.main()
