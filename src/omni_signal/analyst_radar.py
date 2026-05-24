"""Watchlist loading, ticker normalization, and signal collection."""

from __future__ import annotations

import json
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .fmp_client import FMPClient
from .fmp_parsers import (
    parse_analyst_estimates,
    parse_price_target_consensus,
    parse_price_target_summary,
    parse_ratings_snapshot,
)


FULL_ENDPOINT_NAMES = [
    "price_target_consensus",
    "price_target_summary",
    "analyst_estimates",
    "ratings_snapshot",
]

SUMMARY_ENDPOINT_NAMES = [
    "price_target_consensus",
    "price_target_summary",
]

ENDPOINT_NAMES = list(FULL_ENDPOINT_NAMES)


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


def get_enabled_endpoint_names(summary_only: bool = False) -> List[str]:
    return list(SUMMARY_ENDPOINT_NAMES if summary_only else FULL_ENDPOINT_NAMES)


def collect_ticker_snapshot(
    client: FMPClient,
    ticker: str,
    theme_names: Sequence[str],
    endpoint_names: Sequence[str] = ENDPOINT_NAMES,
) -> Dict[str, Any]:
    collected_at = datetime.now(timezone.utc).isoformat()
    snapshot = {
        "ticker": ticker,
        "theme_names": list(theme_names),
        "price_target": {},
        "price_target_summary": {},
        "analyst_estimates": [],
        "ratings_snapshot": {},
        "collected_at": collected_at,
    }
    if "price_target_consensus" in endpoint_names:
        snapshot["price_target"] = parse_price_target_consensus(
            client.get_price_target_consensus(ticker)
        )
    if "price_target_summary" in endpoint_names:
        snapshot["price_target_summary"] = parse_price_target_summary(
            client.get_price_target_summary(ticker)
        )
    if "analyst_estimates" in endpoint_names:
        snapshot["analyst_estimates"] = parse_analyst_estimates(
            client.get_analyst_estimates(ticker)
        )
    if "ratings_snapshot" in endpoint_names:
        snapshot["ratings_snapshot"] = parse_ratings_snapshot(
            client.get_ratings_snapshot(ticker)
        )
    return snapshot


def collect_radar_data(
    client: FMPClient,
    watchlist: Mapping[str, Sequence[str]],
    *,
    tickers: Optional[Sequence[str]] = None,
    themes: Optional[Sequence[str]] = None,
    max_tickers: Optional[int] = None,
    endpoint_names: Sequence[str] = ENDPOINT_NAMES,
) -> Tuple[RadarRunPlan, List[Dict[str, Any]]]:
    selected_themes, unique_tickers = select_tickers(
        watchlist, tickers=tickers, themes=themes, max_tickers=max_tickers
    )
    theme_map = _theme_map(watchlist)
    snapshots: List[Dict[str, Any]] = []
    for ticker in unique_tickers:
        snapshots.append(
            collect_ticker_snapshot(
                client, ticker, theme_map.get(ticker, []), endpoint_names=endpoint_names
            )
        )
    plan = RadarRunPlan(
        selected_themes=selected_themes,
        selected_tickers=list(tickers) if tickers else [],
        unique_tickers=unique_tickers,
        estimated_call_count=estimate_call_count(unique_tickers, endpoint_names),
        endpoint_names=list(endpoint_names),
    )
    return plan, snapshots


def _theme_map(watchlist: Mapping[str, Sequence[str]]) -> Dict[str, List[str]]:
    mapping: Dict[str, List[str]] = defaultdict(list)
    for theme_name, tickers in watchlist.items():
        for ticker in tickers:
            if theme_name not in mapping[ticker]:
                mapping[ticker].append(theme_name)
    return mapping


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
    latest_estimate = analyst_estimates[0] if analyst_estimates and isinstance(analyst_estimates[0], Mapping) else {}
    return {
        "current_price": _pick_first(
            price_target,
            "current_price",
            "price",
            "currentPrice",
            "current_price",
        )
        or _pick_first(price_target_summary, "current_price", "price", "currentPrice"),
        "consensus_price_target": _pick_first(
            price_target,
            "consensus_price_target",
            "consensusPriceTarget",
            "targetConsensus",
            "target_price",
            "meanTargetPrice",
            "avgPriceTarget",
        ),
        "average_price_target": _pick_first(
            price_target_summary,
            "average_price_target",
            "averagePriceTarget",
            "avgPriceTarget",
            "priceTarget",
            "consensusPriceTarget",
            "meanTargetPrice",
        )
        or _pick_first(
            price_target,
            "consensus_price_target",
            "consensusPriceTarget",
            "targetConsensus",
            "target_price",
            "meanTargetPrice",
            "avgPriceTarget",
        ),
        "rating": _pick_first(
            ratings_snapshot,
            "rating",
            "overallRating",
            "analystRating",
            "recommendation",
        ),
        "rating_score": _pick_first(
            ratings_snapshot, "rating_score", "score", "overallScore", "ratingScore"
        ),
        "estimate_eps_current": _pick_first(
            latest_estimate,
            "estimated_eps_avg",
            "estimatedEpsAvg",
            "epsEstimateAvg",
            "epsAvg",
            "eps",
        ),
        "estimate_eps_previous": _pick_first(
            latest_estimate,
            "estimated_eps_avg_prior",
            "estimatedEpsAvgPrior",
            "epsEstimateAvgPrior",
            "epsAvgPrior",
            "previousEps",
        ),
        "estimate_revision_direction": latest_estimate.get("revision_direction"),
        "analyst_count": _pick_first(
            price_target,
            "analyst_count",
            "numberOfAnalysts",
            "analystsCount",
            "analystCount",
            "numAnalysts",
        )
        or _pick_first(
            price_target_summary,
            "analyst_count",
            "numberOfAnalysts",
            "analystsCount",
            "analystCount",
            "numAnalysts",
        ),
    }


def _pick_first(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value not in (None, "", []):
            return value
    return None
