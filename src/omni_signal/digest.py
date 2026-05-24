"""Digest rendering for the FMP analyst radar prototype."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence


def build_digest_report(
    *,
    run_metadata: Mapping[str, Any],
    snapshots: Sequence[Mapping[str, Any]],
    scored: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    scored_by_ticker = {item["ticker"]: dict(item) for item in scored}
    ordered_scored = sorted(scored_by_ticker.values(), key=lambda item: item["score"], reverse=True)
    theme_counts = Counter()
    missing = []
    ticker_details = []

    for snapshot in snapshots:
        ticker = snapshot.get("ticker")
        score_entry = scored_by_ticker.get(ticker, {})
        themes = list(snapshot.get("theme_names") or [])
        for theme in themes:
            theme_counts[theme] += 1

        issues = _missing_issues(snapshot)
        if issues:
            missing.append({"ticker": ticker, "issues": issues})

        ticker_details.append(
            {
                "ticker": ticker,
                "score": score_entry.get("score"),
                "confidence": score_entry.get("confidence"),
                "signals": score_entry.get("signals", []),
                "theme_names": themes,
                "price_target": snapshot.get("price_target", {}),
                "price_target_summary": snapshot.get("price_target_summary", {}),
                "ratings_snapshot": snapshot.get("ratings_snapshot", {}),
                "analyst_estimates": snapshot.get("analyst_estimates", []),
            }
        )

    top_signals = ordered_scored[:5]
    theme_summary = [
        {"theme": theme, "ticker_count": count}
        for theme, count in sorted(theme_counts.items(), key=lambda item: (-item[1], item[0]))
    ]
    report = {
        "title": "FMP Analyst Radar Digest",
        "disclaimer": "This is not investment advice. It is an analyst-signal monitoring digest.",
        "run_metadata": dict(run_metadata),
        "top_signals": top_signals,
        "theme_summary": theme_summary,
        "ticker_details": ticker_details,
        "missing_or_incomplete_data": missing,
        "next_actions": [
            "Review the tickers with the strongest upside or improving estimate trends.",
            "Cross-check FMP signals with your own thesis, fundamentals, and risk controls.",
            "Expand coverage only after the free-tier call budget remains comfortable.",
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return report


def render_markdown(report: Mapping[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# FMP Analyst Radar Digest")
    lines.append("")
    lines.append(report.get("disclaimer", "This is not investment advice."))
    lines.append("")
    lines.append("## Run Metadata")
    metadata = report.get("run_metadata", {})
    for key in [
        "generated_at",
        "watchlist_path",
        "selected_themes",
        "selected_tickers",
        "unique_tickers",
        "endpoint_names",
        "estimated_call_count",
        "dry_run",
    ]:
        value = metadata.get(key)
        lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    lines.append("")

    lines.append("## Top Signals")
    top_signals = report.get("top_signals", [])
    if top_signals:
        for item in top_signals:
            signals = "; ".join(item.get("signals", []))
            lines.append(
                f"- {item.get('ticker')}: score {item.get('score')} "
                f"({item.get('confidence')} confidence) - {signals}"
            )
    else:
        lines.append("- No signals available.")
    lines.append("")

    lines.append("## Theme Summary")
    theme_summary = report.get("theme_summary", [])
    if theme_summary:
        for row in theme_summary:
            lines.append(f"- {row.get('theme')}: {row.get('ticker_count')} tickers")
    else:
        lines.append("- No theme summary available.")
    lines.append("")

    lines.append("## Ticker Details")
    for item in report.get("ticker_details", []):
        theme_names = item.get("theme_names") or []
        signals = item.get("signals") or []
        detail_bits = [f"score {item.get('score')}", f"{item.get('confidence')} confidence"]
        if theme_names:
            detail_bits.append(f"themes: {', '.join(theme_names)}")
        if signals:
            detail_bits.append(f"signals: {', '.join(signals)}")
        lines.append(f"- {item.get('ticker')}: " + "; ".join(detail_bits))
    if not report.get("ticker_details"):
        lines.append("- No ticker details available.")
    lines.append("")

    lines.append("## Missing/Incomplete Data")
    missing = report.get("missing_or_incomplete_data", [])
    if missing:
        for row in missing:
            lines.append(f"- {row.get('ticker')}: {', '.join(row.get('issues', []))}")
    else:
        lines.append("- No missing or incomplete data detected.")
    lines.append("")

    lines.append("## Next Actions")
    for action in report.get("next_actions", []):
        lines.append(f"- {action}")
    lines.append("")
    return "\n".join(lines)


def write_digest_outputs(report: Mapping[str, Any], output_dir: str | Path) -> Dict[str, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    json_path = output_path / "latest.json"
    md_path = output_path / "latest.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}


def _missing_issues(snapshot: Mapping[str, Any]) -> List[str]:
    issues: List[str] = []
    if not snapshot.get("price_target"):
        issues.append("price target missing")
    if not snapshot.get("price_target_summary"):
        issues.append("price target summary missing")
    if not snapshot.get("analyst_estimates"):
        issues.append("analyst estimates missing")
    if not snapshot.get("ratings_snapshot"):
        issues.append("ratings snapshot missing")
    return issues
