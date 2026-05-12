from pathlib import Path

from omni_signal.models import ScoredSignal


def generate_report(scored: list[ScoredSignal], out_path: str) -> str:
    lines = ["# Omni Signal Daily Report", "", "| Symbol | Source | Score | Blocked | Reason |", "|---|---:|---:|---:|---|"]
    for s in scored:
        lines.append(f"| {s.signal.symbol} | {s.signal.source} | {s.score:.2f} | {s.blocked} | {s.reason} |")
    text = "\n".join(lines) + "\n"
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(text, encoding="utf-8")
    return text
