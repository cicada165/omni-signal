"""Endpoint-specific response parsers for FMP analyst radar data."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Sequence


def parse_price_target_consensus(payload: Any) -> Dict[str, Any]:
    record = _first_record(payload)
    return {
        "current_price": _first_present(record, "price", "currentPrice", "current_price"),
        "consensus_price_target": _first_present(
            record,
            "consensusPriceTarget",
            "consensus_price_target",
            "targetConsensus",
            "target_price",
            "meanTargetPrice",
            "avgPriceTarget",
        ),
        "high_price_target": _first_present(
            record, "highPriceTarget", "high_price_target", "targetHigh"
        ),
        "low_price_target": _first_present(
            record, "lowPriceTarget", "low_price_target", "targetLow"
        ),
        "median_price_target": _first_present(
            record, "medianPriceTarget", "median_price_target", "targetMedian"
        ),
        "analyst_count": _first_present(
            record, "numberOfAnalysts", "analystsCount", "analystCount", "numAnalysts"
        ),
        "raw": record,
        "records": _records(payload),
    }


def parse_price_target_summary(payload: Any) -> Dict[str, Any]:
    record = _first_record(payload)
    return {
        "current_price": _first_present(record, "price", "currentPrice", "current_price"),
        "average_price_target": _first_present(
            record,
            "averagePriceTarget",
            "avgPriceTarget",
            "priceTarget",
            "consensusPriceTarget",
            "meanTargetPrice",
        ),
        "previous_price_target": _first_present(
            record,
            "previousPriceTarget",
            "priorPriceTarget",
            "lastPriceTarget",
            "priceTargetPrev",
        ),
        "analyst_count": _first_present(
            record, "numberOfAnalysts", "analystsCount", "analystCount", "numAnalysts"
        ),
        "raw": record,
        "records": _records(payload),
    }


def parse_analyst_estimates(payload: Any) -> List[Dict[str, Any]]:
    records = _records(payload)
    parsed: List[Dict[str, Any]] = []
    for record in records:
        eps_current = _first_present(
            record,
            "estimatedEpsAvg",
            "epsEstimateAvg",
            "epsAvg",
            "eps",
        )
        eps_previous = _first_present(
            record,
            "estimatedEpsAvgPrior",
            "epsEstimateAvgPrior",
            "epsAvgPrior",
            "previousEps",
        )
        parsed.append(
            {
                "period": _first_present(record, "period", "fiscalPeriod"),
                "calendar_year": _first_present(record, "calendarYear", "year"),
                "estimated_eps_avg": eps_current,
                "estimated_eps_avg_prior": eps_previous,
                "estimated_revenue_avg": _first_present(
                    record,
                    "estimatedRevenueAvg",
                    "revenueEstimateAvg",
                    "revenueAvg",
                    "revenue",
                ),
                "estimated_revenue_avg_prior": _first_present(
                    record,
                    "estimatedRevenueAvgPrior",
                    "revenueEstimateAvgPrior",
                    "revenueAvgPrior",
                    "previousRevenue",
                ),
                "revision_direction": _revision_direction(eps_current, eps_previous),
                "raw": record,
            }
        )
    return parsed


def parse_ratings_snapshot(payload: Any) -> Dict[str, Any]:
    record = _first_record(payload)
    return {
        "rating": _first_present(
            record, "overallRating", "rating", "analystRating", "recommendation"
        ),
        "rating_score": _first_present(record, "score", "overallScore", "ratingScore"),
        "dcf_score": _first_present(record, "dcfScore"),
        "roe_score": _first_present(record, "roeScore"),
        "roa_score": _first_present(record, "roaScore"),
        "debt_to_equity_score": _first_present(record, "debtToEquityScore"),
        "pe_score": _first_present(record, "peScore"),
        "pb_score": _first_present(record, "pbScore"),
        "raw": record,
        "records": _records(payload),
    }


def _records(payload: Any) -> List[Dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("data", "results", "historical", "historicalData"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [payload]
    return []


def _first_record(payload: Any) -> Dict[str, Any]:
    records = _records(payload)
    return records[0] if records else {}


def _first_present(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value not in (None, "", []):
            return value
    return None


def _revision_direction(current: Any, previous: Any) -> str | None:
    current_num = _as_float(current)
    previous_num = _as_float(previous)
    if current_num is None or previous_num is None:
        return None
    if current_num > previous_num:
        return "up"
    if current_num < previous_num:
        return "down"
    return "flat"


def _as_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
