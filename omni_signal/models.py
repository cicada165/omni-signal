from dataclasses import dataclass


@dataclass
class Signal:
    symbol: str
    source: str
    confidence: float
    direction: str = "buy"
    is_option: bool = False
    wash_sale_candidate: bool = False
    wealthfront_overlap_etf: bool = False


@dataclass
class ScoredSignal:
    signal: Signal
    score: float
    blocked: bool
    reason: str = ""
