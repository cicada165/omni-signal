"""Small Financial Modeling Prep client for analyst-signal monitoring."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl, quote_plus
from urllib.request import Request, urlopen


class FMPClientError(RuntimeError):
    """Raised when an FMP request fails."""


@dataclass(frozen=True)
class FMPPaths:
    analyst_estimates: str = "/analyst-estimates"
    price_target_consensus: str = "/price-target-consensus"
    price_target_summary: str = "/price-target-summary"
    ratings_snapshot: str = "/ratings-snapshot"


class FMPClient:
    """Minimal FMP client with env-based API key lookup and safe errors."""

    def __init__(
        self,
        base_url: str = "https://financialmodelingprep.com/stable",
        timeout: float = 10.0,
        paths: Optional[FMPPaths] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.paths = paths or FMPPaths()
        self.api_key = os.getenv("FMP_API_KEY")
        if not self.api_key:
            raise FMPClientError("Missing FMP_API_KEY environment variable.")

    def build_url(self, path: str, params: Optional[Mapping[str, Any]] = None) -> str:
        """Build a request URL with the API key attached."""
        query = dict(params or {})
        query["apikey"] = self.api_key
        return f"{self.base_url}/{path.lstrip('/')}?{urlencode(query)}"

    @staticmethod
    def redact_url(url: str) -> str:
        """Return a URL with sensitive parameters removed for logs/errors."""
        parsed = urlparse(url)
        redacted_pairs = []
        for key, value in parse_qsl(parsed.query, keep_blank_values=True):
            if key.lower() in {"apikey", "api_key", "key"}:
                redacted_pairs.append(f"{quote_plus(key)}=[redacted]")
            else:
                redacted_pairs.append(f"{quote_plus(key)}={quote_plus(value)}")
        redacted_query = "&".join(redacted_pairs)
        return urlunparse(parsed._replace(query=redacted_query))

    def _get_json(self, path: str, params: Optional[Mapping[str, Any]] = None) -> Any:
        url = self.build_url(path, params)
        request = Request(url, headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8")  # type: ignore[attr-defined]
            except Exception:
                body = ""
            detail = f": {body.strip()}" if body.strip() else ""
            raise FMPClientError(
                f"FMP request failed for {path} with HTTP {exc.code}{detail}"
            ) from exc
        except URLError as exc:
            raise FMPClientError(f"FMP request failed for {path}: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise FMPClientError(f"FMP returned invalid JSON for {path}") from exc

    def get_price_target_consensus(self, symbol: str) -> Any:
        return self._get_json(self.paths.price_target_consensus, {"symbol": symbol})

    def get_price_target_summary(self, symbol: str) -> Any:
        return self._get_json(self.paths.price_target_summary, {"symbol": symbol})

    def get_analyst_estimates(
        self,
        symbol: str,
        period: str = "annual",
        page: int = 0,
        limit: int = 10,
    ) -> Any:
        return self._get_json(
            self.paths.analyst_estimates,
            {"symbol": symbol, "period": period, "page": page, "limit": limit},
        )

    def get_ratings_snapshot(self, symbol: str) -> Any:
        return self._get_json(self.paths.ratings_snapshot, {"symbol": symbol})
