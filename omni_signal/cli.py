import argparse
from pathlib import Path

from omni_signal.config import AppConfig
from omni_signal.ingestion.parsers import ingest_csv_signals, ingest_discord_export
from omni_signal.normalize import normalize_signals
from omni_signal.report import generate_report
from omni_signal.risk import apply_risk_checks
from omni_signal.scoring import score_signals


def cmd_init_db() -> int:
    Path("data").mkdir(exist_ok=True)
    Path("data/app.db").touch()
    print("Initialized offline db")
    return 0


def cmd_ingest_examples() -> int:
    Path("data").mkdir(exist_ok=True)
    Path("data/discord_export.json").write_text('[{"symbol":"AAPL","confidence":0.8}]', encoding="utf-8")
    Path("data/kavout.csv").write_text("symbol,score\nMSFT,0.7\n", encoding="utf-8")
    Path("data/sterling.csv").write_text("ticker,confidence\nNVDA,0.9\n", encoding="utf-8")
    print("Wrote sample inputs")
    return 0


def cmd_score() -> int:
    sigs = []
    for p in ["data/discord_export.json", "data/kavout.csv", "data/sterling.csv"]:
        if Path(p).exists():
            if p.endswith(".json"):
                sigs.extend(ingest_discord_export(p))
            elif "kavout" in p:
                sigs.extend(ingest_csv_signals(p, "kavout"))
            else:
                sigs.extend(ingest_csv_signals(p, "sterling"))
    generate_report(apply_risk_checks(score_signals(normalize_signals(sigs)), AppConfig().safety), "reports/daily.md")
    print("Scored signals and generated reports/daily.md")
    return 0


def cmd_report(out: str) -> int:
    src = Path("reports/daily.md")
    if not src.exists():
        print("Run score first")
        return 1
    if out != "reports/daily.md":
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Report available at {out}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="omni-signal")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init-db")
    sub.add_parser("ingest-examples")
    sub.add_parser("score")
    p_report = sub.add_parser("report")
    p_report.add_argument("--out", default="reports/daily.md")
    args = parser.parse_args()
    if args.cmd == "init-db":
        return cmd_init_db()
    if args.cmd == "ingest-examples":
        return cmd_ingest_examples()
    if args.cmd == "score":
        return cmd_score()
    if args.cmd == "report":
        return cmd_report(args.out)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
