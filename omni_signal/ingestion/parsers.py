import csv
import json
from pathlib import Path

from omni_signal.models import Signal


def ingest_discord_export(path: str) -> list[Signal]:
    data = json.loads(Path(path).read_text())
    out: list[Signal] = []
    for msg in data:
        symbol = msg.get("symbol") or msg.get("ticker")
        if not symbol:
            continue
        out.append(Signal(symbol=symbol.upper(), source="discord", confidence=float(msg.get("confidence", 0.5))))
    return out


def ingest_csv_signals(path: str, source: str) -> list[Signal]:
    out: list[Signal] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = (row.get("symbol") or row.get("ticker") or "").upper()
            if not symbol:
                continue
            conf = float(row.get("confidence") or row.get("score") or 0.5)
            out.append(Signal(symbol=symbol, source=source, confidence=conf))
    return out


def ingest_portfolio_csv(path: str) -> list[str]:
    symbols: list[str] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = (row.get("symbol") or row.get("ticker") or "").upper()
            if symbol:
                symbols.append(symbol)
    return symbols
