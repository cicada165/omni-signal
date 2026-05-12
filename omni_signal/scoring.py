from collections import Counter

from omni_signal.models import ScoredSignal, Signal


def score_signals(signals: list[Signal]) -> list[ScoredSignal]:
    counts = Counter(s.symbol for s in signals)
    scored: list[ScoredSignal] = []
    for s in signals:
        multi_source_bonus = 0.2 if counts[s.symbol] > 1 else 0.0
        score = min(1.0, max(0.0, s.confidence + multi_source_bonus))
        scored.append(ScoredSignal(signal=s, score=score, blocked=False))
    return scored
