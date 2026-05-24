"""Explainable scoring for analyst-signal monitoring."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Sequence

from .analyst_radar import extract_metric_fields


def score_snapshot(snapshot: Mapping[str, Any]) -> Dict[str, Any]:
    metrics = extract_metric_fields(snapshot)
    score = 50
    signals = []
    completeness = 0
    total_checks = 4

    current_price = _as_float(metrics.get("current_price"))
    consensus_target = _as_float(metrics.get("consensus_price_target"))
    average_target = _as_float(metrics.get("average_price_target"))
    rating = _normalize_rating(metrics.get("rating"))
    rating_score = _as_float(metrics.get("rating_score"))
    eps_current = _as_float(metrics.get("estimate_eps_current"))
    eps_previous = _as_float(metrics.get("estimate_eps_previous"))
    revision_direction = metrics.get("estimate_revision_direction")

    target_value = consensus_target if consensus_target is not None else average_target
    if current_price is not None and target_value is not None:
        completeness += 1
        upside = (target_value - current_price) / current_price if current_price else 0.0
        if upside >= 0.10:
            score += 15
            signals.append("price target upside detected")
        elif upside > 0:
            score += 8
            signals.append("price target modest upside")
        elif upside < -0.05:
            score -= 12
            signals.append("price target downside detected")
        else:
            signals.append("price target near current price")
    else:
        score -= 8
        signals.append("price target data incomplete")

    if rating is not None or rating_score is not None:
        completeness += 1
        favorable = False
        if rating is not None:
            favorable = rating in {"buy", "strong_buy", "outperform", "overweight", "positive"}
            if favorable:
                score += 12
                signals.append("ratings snapshot favorable")
            else:
                score -= 8
                signals.append("ratings snapshot cautious")
        if rating_score is not None:
            if rating_score >= 70:
                score += 8
                signals.append("ratings snapshot score supportive")
            elif rating_score <= 40:
                score -= 8
                signals.append("ratings snapshot score weak")
    else:
        score -= 8
        signals.append("ratings snapshot missing")

    if eps_current is not None and eps_previous is not None:
        completeness += 1
        if eps_current > eps_previous:
            score += 10
            signals.append("estimate revisions trending upward")
        elif eps_current < eps_previous:
            score -= 10
            signals.append("estimate revisions trending lower")
        else:
            signals.append("estimate revisions flat")
    elif revision_direction in {"up", "down", "flat"}:
        completeness += 1
        if revision_direction == "up":
            score += 8
            signals.append("estimate revisions trending upward")
        elif revision_direction == "down":
            score -= 8
            signals.append("estimate revisions trending lower")
        else:
            signals.append("estimate revisions flat")
    else:
        score -= 6
        signals.append("estimate data incomplete")

    if metrics.get("average_price_target") is not None or metrics.get("consensus_price_target") is not None:
        completeness += 1

    completeness_ratio = completeness / total_checks
    if completeness_ratio >= 0.75:
        confidence = "high"
    elif completeness_ratio >= 0.5:
        confidence = "medium"
    else:
        confidence = "low"
        score -= 5

    score = max(0, min(100, int(round(score))))
    if not signals:
        signals.append("no analyzable signals")
    return {
        "ticker": snapshot.get("ticker"),
        "score": score,
        "confidence": confidence,
        "signals": signals,
        "theme_names": list(snapshot.get("theme_names") or []),
    }


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _normalize_rating(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower().replace(" ", "_")
    return text or None
