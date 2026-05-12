from omni_signal.models import Signal


def normalize_signals(signals: list[Signal]) -> list[Signal]:
    dedup: dict[tuple[str, str], Signal] = {}
    for s in signals:
        s.symbol = s.symbol.strip().upper()
        key = (s.symbol, s.source)
        dedup[key] = s
    return list(dedup.values())
