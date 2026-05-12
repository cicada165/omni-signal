from omni_signal.config import SafetyConfig
from omni_signal.models import ScoredSignal


def apply_risk_checks(scored: list[ScoredSignal], safety: SafetyConfig) -> list[ScoredSignal]:
    for item in scored:
        s = item.signal
        if safety.require_manual_approval_for_options and s.is_option:
            item.blocked = True
            item.reason = "options require manual approval"
        elif safety.block_wash_sale_candidates and s.wash_sale_candidate:
            item.blocked = True
            item.reason = "wash sale candidate"
        elif safety.block_wealthfront_overlap_etfs_in_robinhood and s.wealthfront_overlap_etf:
            item.blocked = True
            item.reason = "wealthfront overlap"
    return scored
