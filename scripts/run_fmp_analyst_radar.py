#!/usr/bin/env python3
"""Run the FMP analyst radar prototype and write local digest outputs."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from omni_signal.analyst_radar import (
    ENDPOINT_NAMES,
    collect_radar_data,
    estimate_call_count,
    get_enabled_endpoint_names,
    load_watchlist,
    select_tickers,
)
from omni_signal.digest import build_digest_report, write_digest_outputs
from omni_signal.fmp_client import FMPClient, FMPClientError
from omni_signal.scoring import score_snapshot


def parse_csv(value: Optional[str]) -> Optional[List[str]]:
    if value is None:
        return None
    parts = [item.strip() for item in value.split(",")]
    cleaned = [item for item in parts if item]
    return cleaned or None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the FMP analyst radar prototype.")
    parser.add_argument(
        "--watchlist",
        required=True,
        help="Path to a theme-based watchlist JSON file.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/digests",
        help="Directory for latest.json and latest.md.",
    )
    parser.add_argument(
        "--tickers",
        help="Comma-separated ticker filter, e.g. NVDA,AMD,MU.",
    )
    parser.add_argument(
        "--themes",
        help="Comma-separated theme filter, e.g. memory_hbm,semiconductor_cycle.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and estimate calls without hitting FMP.",
    )
    parser.add_argument(
        "--summary-only",
        "--theme-summary-only",
        dest="summary_only",
        action="store_true",
        help="Fetch only price-target endpoints to minimize call volume.",
    )
    parser.add_argument(
        "--max-tickers",
        type=int,
        help="Limit the number of unique tickers after filtering and deduplication.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow call estimates above the hard budget threshold.",
    )
    parser.add_argument(
        "--cache-dir",
        help="Optional local response cache directory for repeat live runs.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    watchlist = load_watchlist(args.watchlist)
    selected_tickers = parse_csv(args.tickers)
    selected_themes = parse_csv(args.themes)
    endpoint_names = get_enabled_endpoint_names(args.summary_only)
    _, unique_tickers = select_tickers(
        watchlist,
        tickers=selected_tickers,
        themes=selected_themes,
        max_tickers=args.max_tickers,
    )
    estimated_call_count = estimate_call_count(unique_tickers, endpoint_names)

    print("Planned FMP analyst radar run")
    print(f"- watchlist: {args.watchlist}")
    print(f"- unique tickers: {len(unique_tickers)}")
    print(f"- endpoints per ticker: {len(endpoint_names)}")
    print(f"- estimated calls: {estimated_call_count}")
    print(f"- mode: {'summary-only' if args.summary_only else 'full'}")
    if unique_tickers:
        print(f"- tickers: {', '.join(unique_tickers)}")
    else:
        print("- tickers: none selected")

    if estimated_call_count > 200:
        print(
            f"WARNING: estimated calls {estimated_call_count} exceed the soft budget of 200.",
            file=sys.stderr,
        )
    if estimated_call_count > 250 and not args.force:
        print(
            "ERROR: estimated calls exceed 250. Re-run with --force if you really want to proceed.",
            file=sys.stderr,
        )
        return 2

    if args.dry_run:
        print("Dry run only: no FMP calls were made.")
        return 0

    try:
        client = FMPClient(cache_dir=args.cache_dir)
        plan, snapshots = collect_radar_data(
            client,
            watchlist,
            tickers=selected_tickers,
            themes=selected_themes,
            max_tickers=args.max_tickers,
            endpoint_names=endpoint_names,
        )
    except FMPClientError as exc:
        print(f"FMP client error: {exc}", file=sys.stderr)
        return 1

    scored = [score_snapshot(snapshot) for snapshot in snapshots]
    metadata = {
        "generated_at": snapshots[0]["collected_at"] if snapshots else None,
        "watchlist_path": str(Path(args.watchlist).resolve()),
        "selected_themes": plan.selected_themes,
        "selected_tickers": plan.selected_tickers,
        "unique_tickers": plan.unique_tickers,
        "endpoint_names": plan.endpoint_names,
        "summary_only": args.summary_only,
        "cache_dir": args.cache_dir,
        "estimated_call_count": plan.estimated_call_count,
        "dry_run": False,
    }
    report = build_digest_report(
        run_metadata=metadata,
        snapshots=snapshots,
        scored=scored,
    )
    outputs = write_digest_outputs(report, args.output_dir)
    print(f"Wrote digest JSON: {outputs['json']}")
    print(f"Wrote digest Markdown: {outputs['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
