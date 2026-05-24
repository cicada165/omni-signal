import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from omni_signal.analyst_radar import estimate_call_count, load_watchlist, select_tickers
from omni_signal.digest import build_digest_report, render_markdown, write_digest_outputs


class TestDigest(unittest.TestCase):
    def test_watchlist_loading_and_deduplication(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "watchlist.json"
            path.write_text(
                json.dumps(
                    {
                        "theme_a": ["NVDA", "AMD", "NVDA"],
                        "theme_b": ["AMD", "MU"],
                    }
                ),
                encoding="utf-8",
            )
            watchlist = load_watchlist(path)
            themes, tickers = select_tickers(watchlist)
            self.assertEqual(themes, ["theme_a", "theme_b"])
            self.assertEqual(tickers, ["NVDA", "AMD", "MU"])
            self.assertEqual(estimate_call_count(tickers), 12)

    def test_markdown_digest_generation(self) -> None:
        report = build_digest_report(
            run_metadata={
                "generated_at": "2026-05-23T00:00:00Z",
                "watchlist_path": "/tmp/watchlist.json",
                "selected_themes": ["memory_hbm"],
                "selected_tickers": [],
                "unique_tickers": ["NVDA"],
                "endpoint_names": ["price_target_consensus"],
                "estimated_call_count": 1,
                "dry_run": False,
            },
            snapshots=[
                {
                    "ticker": "NVDA",
                    "theme_names": ["memory_hbm"],
                    "price_target": {"consensusPriceTarget": 150},
                    "price_target_summary": {"averagePriceTarget": 155},
                    "analyst_estimates": [{"estimatedEpsAvg": 5.5, "estimatedEpsAvgPrior": 5.0}],
                    "ratings_snapshot": {"overallRating": "buy"},
                }
            ],
            scored=[
                {
                    "ticker": "NVDA",
                    "score": 82,
                    "confidence": "high",
                    "signals": ["price target upside detected"],
                    "theme_names": ["memory_hbm"],
                }
            ],
        )
        markdown = render_markdown(report)
        self.assertIn("FMP Analyst Radar Digest", markdown)
        self.assertIn("This is not investment advice", markdown)
        self.assertIn("Top Signals", markdown)
        self.assertIn("NVDA", markdown)

    def test_write_digest_outputs(self) -> None:
        report = {
            "title": "FMP Analyst Radar Digest",
            "disclaimer": "This is not investment advice. It is an analyst-signal monitoring digest.",
            "run_metadata": {
                "generated_at": "2026-05-23T00:00:00Z",
                "watchlist_path": "/tmp/watchlist.json",
                "selected_themes": ["memory_hbm"],
                "selected_tickers": [],
                "unique_tickers": ["NVDA"],
                "endpoint_names": ["price_target_consensus"],
                "estimated_call_count": 1,
                "dry_run": False,
            },
            "top_signals": [],
            "theme_summary": [],
            "ticker_details": [],
            "missing_or_incomplete_data": [],
            "next_actions": [],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            outputs = write_digest_outputs(report, tmpdir)
            self.assertTrue(outputs["json"].exists())
            self.assertTrue(outputs["markdown"].exists())
            self.assertIn("latest.json", str(outputs["json"]))

    def test_cli_dry_run_estimates_calls(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            watchlist = Path(tmpdir) / "watchlist.json"
            watchlist.write_text(
                json.dumps({"theme_a": ["NVDA", "AMD"], "theme_b": ["AMD", "MU"]}),
                encoding="utf-8",
            )
            env = dict(os.environ)
            env.pop("FMP_API_KEY", None)
            env["PYTHONPATH"] = "src"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_fmp_analyst_radar.py",
                    "--watchlist",
                    str(watchlist),
                    "--output-dir",
                    str(Path(tmpdir) / "out"),
                    "--dry-run",
                ],
                cwd=Path(__file__).resolve().parents[1],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("estimated calls: 12", result.stdout)
