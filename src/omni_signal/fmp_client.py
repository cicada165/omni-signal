"""Small Financial Modeling Prep client for analyst-signal monitoring."""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
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
        cache_dir: str | Path | None = None,
        cache_ttl_seconds: int = 24 * 60 * 60,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.paths = paths or FMPPaths()
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.cache_ttl_seconds = cache_ttl_seconds
        self.api_key = os.getenv("FMP_API_KEY")
        if not self.api_key:
            raise FMPClientError("Missing FMP_API_KEY environment variable.")
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

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
        cache_key = self._cache_key(path, params)
        cached = self._load_cache(cache_key)
        if cached is not None:
            return cached
        url = self.build_url(path, params)
        request = Request(url, headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                data = json.loads(raw) if raw else None
                self._store_cache(cache_key, data)
                return data
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

    def _cache_key(self, path: str, params: Optional[Mapping[str, Any]] = None) -> str:
        query = dict(params or {})
        query.pop("apikey", None)
        query_items = "&".join(f"{key}={query[key]}" for key in sorted(query))
        digest = hashlib.sha256(f"{path}?{query_items}".encode("utf-8")).hexdigest()
        return digest

    def _cache_path(self, cache_key: str) -> Optional[Path]:
        if not self.cache_dir:
            return None
        return self.cache_dir / f"{cache_key}.json"

    def _load_cache(self, cache_key: str) -> Any:
        cache_path = self._cache_path(cache_key)
        if not cache_path or not cache_path.exists():
            return None
        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            return None
        fetched_at = payload.get("fetched_at")
        if not isinstance(fetched_at, (int, float)):
            return None
        if self.cache_ttl_seconds >= 0 and (time.time() - float(fetched_at)) > self.cache_ttl_seconds:
            return None
        return payload.get("data")

    def _store_cache(self, cache_key: str, data: Any) -> None:
        cache_path = self._cache_path(cache_key)
        if not cache_path:
            return
        try:
            cache_path.write_text(
                json.dumps({"fetched_at": time.time(), "data": data}, sort_keys=True),
                encoding="utf-8",
            )
        except Exception:
            return

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
