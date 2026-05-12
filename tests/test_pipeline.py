from omni_signal.config import AppConfig
from omni_signal.models import Signal
from omni_signal.normalize import normalize_signals
from omni_signal.report import generate_report
from omni_signal.risk import apply_risk_checks
from omni_signal.scoring import score_signals


def test_normalization_dedupes():
    signals = [Signal("aapl", "discord", 0.6), Signal("AAPL", "discord", 0.7)]
    out = normalize_signals(signals)
    assert len(out) == 1
    assert out[0].symbol == "AAPL"


def test_scoring_behavior_multi_source_bonus():
    signals = [Signal("AAPL", "discord", 0.5), Signal("AAPL", "kavout", 0.5)]
    scored = score_signals(signals)
    assert all(s.score == 0.7 for s in scored)


def test_risk_blocking_behavior():
    cfg = AppConfig().safety
    signals = [Signal("AAPL", "discord", 0.9, is_option=True)]
    blocked = apply_risk_checks(score_signals(signals), cfg)
    assert blocked[0].blocked is True


def test_report_generation(tmp_path):
    scored = score_signals([Signal("MSFT", "kavout", 0.8)])
    p = tmp_path / "daily.md"
    text = generate_report(scored, str(p))
    assert "Omni Signal Daily Report" in text
    assert p.exists()
