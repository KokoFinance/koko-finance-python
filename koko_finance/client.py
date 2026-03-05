"""
Koko Finance API Client

Wraps the REST API v1 with typed methods and clean error handling.
"""

import requests
from typing import Dict, List, Optional

from .exceptions import (
    KokoError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    ServerError,
)


class KokoClient:
    """Client for the Koko Finance credit card intelligence API.

    Args:
        api_key: Your Koko API key (format: koko_xxxxx)
        base_url: API base URL (default: https://kokofinance.net)
        timeout: Request timeout in seconds (default: 30)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://kokofinance.net",
        timeout: int = 30,
    ):
        if not api_key:
            raise ValueError("api_key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        })

    def _request(self, method: str, path: str, json: dict = None) -> dict:
        """Make an API request and return the unwrapped data.

        Sends the HTTP request, checks for errors, unwraps the APIResponse
        envelope, and returns the `data` field directly.
        """
        url = f"{self._base_url}/api/v1{path}"

        try:
            resp = self._session.request(
                method, url, json=json, timeout=self._timeout
            )
        except requests.ConnectionError as e:
            raise KokoError(f"Connection error: {e}")
        except requests.Timeout:
            raise KokoError(f"Request timed out after {self._timeout}s")

        # Extract request_id from response body if available
        request_id = None
        try:
            body = resp.json()
            request_id = body.get("metadata", {}).get("request_id")
        except (ValueError, AttributeError):
            body = None

        # Map HTTP status codes to exceptions
        if resp.status_code == 401:
            detail = body.get("detail", {}) if body else {}
            message = detail.get("message", "Authentication failed") if isinstance(detail, dict) else str(detail)
            raise AuthenticationError(
                message=message,
                status_code=401,
                request_id=request_id,
            )
        elif resp.status_code == 429:
            detail = body.get("detail", {}) if body else {}
            message = detail.get("message", "Rate limit exceeded") if isinstance(detail, dict) else str(detail)
            retry_after = None
            if "Retry-After" in resp.headers:
                try:
                    retry_after = int(resp.headers["Retry-After"])
                except (ValueError, TypeError):
                    pass
            raise RateLimitError(
                message=message,
                status_code=429,
                request_id=request_id,
                retry_after=retry_after,
            )
        elif resp.status_code in (400, 422):
            detail = body.get("detail", {}) if body else {}
            if isinstance(detail, list):
                # Pydantic validation errors come as a list
                message = "; ".join(
                    f"{e.get('loc', ['?'])[-1]}: {e.get('msg', '?')}" for e in detail
                )
            elif isinstance(detail, dict):
                message = detail.get("message", "Validation error")
            else:
                message = str(detail)
            raise ValidationError(
                message=message,
                status_code=resp.status_code,
                request_id=request_id,
            )
        elif resp.status_code >= 500:
            message = "Internal server error"
            if body:
                detail = body.get("detail", body.get("error", ""))
                if isinstance(detail, dict):
                    message = detail.get("message", message)
                elif detail:
                    message = str(detail)
            raise ServerError(
                message=message,
                status_code=resp.status_code,
                request_id=request_id,
            )
        elif resp.status_code >= 400:
            raise KokoError(
                message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                status_code=resp.status_code,
                request_id=request_id,
            )

        # Unwrap APIResponse envelope — return data directly
        if body and "data" in body:
            return body["data"]
        return body

    def _build_params(
        self,
        spending: Optional[Dict[str, float]] = None,
        primary_goal: Optional[str] = None,
        credit_tier: Optional[str] = None,
        issuer_preferences: Optional[List[dict]] = None,
    ) -> Optional[dict]:
        """Build ClientParameters dict from flat arguments."""
        params = {}
        if spending:
            params["spending"] = spending
        if primary_goal:
            params["primary_goal"] = primary_goal
        if credit_tier:
            params["credit_tier"] = credit_tier
        if issuer_preferences:
            params["issuer_preferences"] = issuer_preferences
        return params if params else None

    def analyze_portfolio(
        self,
        cards: List[dict],
        spending: Optional[Dict[str, float]] = None,
        primary_goal: Optional[str] = None,
        credit_tier: Optional[str] = None,
        issuer_preferences: Optional[List[dict]] = None,
    ) -> dict:
        """Analyze a credit card portfolio for value and optimization.

        Args:
            cards: List of card dicts, e.g. [{"card_name": "Chase Sapphire Preferred", "annual_fee": 95}]
            spending: Monthly spending by category, e.g. {"dining": 500, "travel": 300}
            primary_goal: One of "travel", "cashback", "build_credit", "business", "balance_transfer"
            credit_tier: One of "poor", "fair", "good", "excellent"
            issuer_preferences: List of dicts, e.g. [{"issuer": "Chase", "weight": 1.5}]

        Returns:
            dict with card_calculations, portfolio_summary, recommendations, and analysis
        """
        payload = {"cards": cards}
        params = self._build_params(spending, primary_goal, credit_tier, issuer_preferences)
        if params:
            payload["params"] = params
        return self._request("POST", "/portfolio/analyze", json=payload)

    def compare_cards(
        self,
        cards: List[dict],
        spending: Optional[Dict[str, float]] = None,
        primary_goal: Optional[str] = None,
    ) -> dict:
        """Compare 2-3 credit cards side-by-side.

        Args:
            cards: List of card dicts with card_name (and optionally annual_fee).
                   Note: The API expects card_names as a list of strings.
            spending: Monthly spending by category
            primary_goal: Optimization goal

        Returns:
            dict with comparison_table, winner, and analysis
        """
        # Extract card names for the API (V1CompareRequest uses card_names: List[str])
        card_names = [c["card_name"] if isinstance(c, dict) else c for c in cards]
        payload = {"card_names": card_names}
        params = self._build_params(spending, primary_goal)
        if params:
            payload["params"] = params
        return self._request("POST", "/cards/compare", json=payload)

    def recommend_card(
        self,
        category: str,
        spending: Optional[Dict[str, float]] = None,
        primary_goal: Optional[str] = None,
        credit_tier: Optional[str] = None,
        portfolio_card_names: Optional[List[str]] = None,
    ) -> dict:
        """Get card recommendations for a spending category.

        Args:
            category: Spending category, e.g. "dining", "travel", "groceries", "gas"
            spending: Monthly spending by category
            primary_goal: Optimization goal
            credit_tier: Credit score tier for filtering
            portfolio_card_names: If provided, recommend from portfolio instead of market

        Returns:
            dict with recommended_card, alternatives, and analysis
        """
        payload = {"category": category}
        if portfolio_card_names:
            payload["portfolio_card_names"] = portfolio_card_names
        params = self._build_params(spending, primary_goal, credit_tier)
        if params:
            payload["params"] = params
        return self._request("POST", "/cards/recommend", json=payload)

    def check_renewal(
        self,
        card: dict,
        spending: Optional[Dict[str, float]] = None,
        primary_goal: Optional[str] = None,
    ) -> dict:
        """Check if a card is worth renewing at annual fee time.

        Args:
            card: Card dict, e.g. {"card_name": "Chase Sapphire Preferred", "annual_fee": 95}
            spending: Monthly spending by category
            primary_goal: Optimization goal

        Returns:
            dict with verdict (RENEW/DOWNGRADE/CANCEL_AND_REPLACE), value analysis,
            downgrade_options, and replacement_options
        """
        payload = {"card_name": card["card_name"]}
        if "card_id" in card:
            payload["card_id"] = card["card_id"]
        params = self._build_params(spending, primary_goal)
        if params:
            payload["params"] = params
        return self._request("POST", "/card/renewal-check", json=payload)

    def get_usage(self) -> dict:
        """Get current API usage for your account.

        Note: This endpoint may return 404 until Phase 2.
        """
        return self._request("GET", "/usage")

    def health(self) -> dict:
        """Check API health status. No authentication required."""
        return self._request("GET", "/health")
