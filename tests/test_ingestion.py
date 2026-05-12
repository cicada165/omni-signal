import json
from pathlib import Path

from omni_signal.ingestion.parsers import ingest_csv_signals, ingest_discord_export, ingest_portfolio_csv


def test_discord_ingestion(tmp_path: Path):
    p = tmp_path / "discord.json"
    p.write_text(json.dumps([{"symbol": "aapl", "confidence": 0.9}, {"ticker": "msft"}]))
    out = ingest_discord_export(str(p))
    assert [s.symbol for s in out] == ["AAPL", "MSFT"]


def test_kavout_csv_ingestion(tmp_path: Path):
    p = tmp_path / "kavout.csv"
    p.write_text("symbol,score\nAAPL,0.8\n")
    out = ingest_csv_signals(str(p), "kavout")
    assert out[0].source == "kavout"
    assert out[0].confidence == 0.8


def test_sterling_csv_ingestion(tmp_path: Path):
    p = tmp_path / "sterling.csv"
    p.write_text("ticker,confidence\nNVDA,0.7\n")
    out = ingest_csv_signals(str(p), "sterling")
    assert out[0].symbol == "NVDA"


def test_portfolio_csv_ingestion(tmp_path: Path):
    p = tmp_path / "portfolio.csv"
    p.write_text("symbol,weight\nQQQ,0.2\nSPY,0.8\n")
    out = ingest_portfolio_csv(str(p))
    assert out == ["QQQ", "SPY"]
