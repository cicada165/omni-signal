"""Watchlist loading, ticker normalization, and signal collection."""

from __future__ import annotations

import json
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .fmp_client import FMPClient


ENDPOINT_NAMES = [
    "price_target_consensus",
    "price_target_summary",
    "analyst_estimates",
    "ratings_snapshot",
]


@dataclass(frozen=True)
class RadarRunPlan:
    selected_themes: List[str]
    selected_tickers: List[str]
    unique_tickers: List[str]
    estimated_call_count: int
    endpoint_names: List[str]


def load_watchlist(path: str | Path) -> Dict[str, List[str]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Watchlist must be a JSON object of theme names to tickers.")

    watchlist: Dict[str, List[str]] = {}
    for theme_name, tickers in raw.items():
        if not isinstance(theme_name, str):
            raise ValueError("Theme names must be strings.")
        if not isinstance(tickers, list):
            raise ValueError(f"Theme {theme_name!r} must map to a list of tickers.")
        normalized: List[str] = []
        for ticker in tickers:
            if not isinstance(ticker, str):
                raise ValueError(f"Ticker values in {theme_name!r} must be strings.")
            symbol = ticker.strip().upper()
            if symbol:
                normalized.append(symbol)
        watchlist[theme_name] = normalized
    return watchlist


def select_tickers(
    watchlist: Mapping[str, Sequence[str]],
    *,
    tickers: Optional[Sequence[str]] = None,
    themes: Optional[Sequence[str]] = None,
    max_tickers: Optional[int] = None,
) -> Tuple[List[str], List[str]]:
    selected_themes = list(themes) if themes else list(watchlist.keys())
    selected_tickers = []
    requested = {ticker.strip().upper() for ticker in tickers or [] if ticker.strip()}
    for theme in selected_themes:
        for ticker in watchlist.get(theme, []):
            if requested and ticker not in requested:
                continue
            selected_tickers.append(ticker)

    unique_tickers = list(OrderedDict.fromkeys(selected_tickers))
    if max_tickers is not None:
        unique_tickers = unique_tickers[: max(0, max_tickers)]
    return selected_themes, unique_tickers


def estimate_call_count(unique_tickers: Sequence[str], endpoint_names: Sequence[str] = ENDPOINT_NAMES) -> int:
    return len(list(unique_tickers)) * len(list(endpoint_names))


def collect_ticker_snapshot(
    client: FMPClient,
    ticker: str,
    theme_names: Sequence[str],
) -> Dict[str, Any]:
    collected_at = datetime.now(timezone.utc).isoformat()
    snapshot = {
        "ticker": ticker,
        "theme_names": list(theme_names),
        "price_target": _normalize_object_payload(client.get_price_target_consensus(ticker)),
        "price_target_summary": _normalize_object_payload(client.get_price_target_summary(ticker)),
        "analyst_estimates": _normalize_estimates(client.get_analyst_estimates(ticker)),
        "ratings_snapshot": _normalize_object_payload(client.get_ratings_snapshot(ticker)),
        "collected_at": collected_at,
    }
    return snapshot


def collect_radar_data(
    client: FMPClient,
    watchlist: Mapping[str, Sequence[str]],
    *,
    tickers: Optional[Sequence[str]] = None,
    themes: Optional[Sequence[str]] = None,
    max_tickers: Optional[int] = None,
) -> Tuple[RadarRunPlan, List[Dict[str, Any]]]:
    selected_themes, unique_tickers = select_tickers(
        watchlist, tickers=tickers, themes=themes, max_tickers=max_tickers
    )
    theme_map = _theme_map(watchlist)
    snapshots: List[Dict[str, Any]] = []
    for ticker in unique_tickers:
        snapshots.append(
            collect_ticker_snapshot(client, ticker, theme_map.get(ticker, []))
        )
    plan = RadarRunPlan(
        selected_themes=selected_themes,
        selected_tickers=list(tickers) if tickers else [],
        unique_tickers=unique_tickers,
        estimated_call_count=estimate_call_count(unique_tickers),
        endpoint_names=list(ENDPOINT_NAMES),
    )
    return plan, snapshots


def _theme_map(watchlist: Mapping[str, Sequence[str]]) -> Dict[str, List[str]]:
    mapping: Dict[str, List[str]] = defaultdict(list)
    for theme_name, tickers in watchlist.items():
        for ticker in tickers:
            if theme_name not in mapping[ticker]:
                mapping[ticker].append(theme_name)
    return mapping


def _normalize_object_payload(payload: Any) -> Dict[str, Any]:
    if payload is None:
        return {}
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list):
        if not payload:
            return {}
        first = payload[0]
        if isinstance(first, dict):
            return first
        return {"items": payload}
    return {"value": payload}


def _normalize_estimates(payload: Any) -> List[Dict[str, Any]]:
    if not payload:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        if "data" in payload and isinstance(payload["data"], list):
            return [item for item in payload["data"] if isinstance(item, dict)]
        return [payload]
    return []


def extract_metric_fields(snapshot: Mapping[str, Any]) -> Dict[str, Any]:
    price_target = snapshot.get("price_target") or {}
    price_target_summary = snapshot.get("price_target_summary") or {}
    ratings_snapshot = snapshot.get("ratings_snapshot") or {}
    analyst_estimates = snapshot.get("analyst_estimates") or []
    if not isinstance(price_target, Mapping):
        price_target = {}
    if not isinstance(price_target_summary, Mapping):
        price_target_summary = {}
    if not isinstance(ratings_snapshot, Mapping):
        ratings_snapshot = {}
    if not isinstance(analyst_estimates, list):
        analyst_estimates = []
    latest_estimate = analyst_estimates[0] if analyst_estimates else {}
    return {
        "current_price": _first_present(price_target, "price", "currentPrice", "current_price"),
        "consensus_price_target": _first_present(
            price_target,
            "consensusPriceTarget",
            "consensus_price_target",
            "targetConsensus",
            "target_price",
        ),
        "average_price_target": _first_present(
            price_target_summary,
            "averagePriceTarget",
            "avgPriceTarget",
            "priceTarget",
            "consensusPriceTarget",
        ),
        "rating": _first_present(
            ratings_snapshot,
            "rating",
            "overallRating",
            "analystRating",
            "recommendation",
        ),
        "rating_score": _first_present(
            ratings_snapshot,
            "score",
            "overallScore",
            "ratingScore",
        ),
        "estimate_eps_current": _first_present(
            latest_estimate, "estimatedEpsAvg", "epsEstimateAvg", "epsAvg", "eps"
        ),
        "estimate_eps_previous": _first_present(
            latest_estimate,
            "estimatedEpsAvgPrior",
            "epsEstimateAvgPrior",
            "epsAvgPrior",
            "previousEps",
        ),
    }


def _first_present(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value not in (None, "", []):
            return value
    return None
