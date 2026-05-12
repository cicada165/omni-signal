from dataclasses import dataclass, field


@dataclass
class FeatureFlags:
    enable_live_discord_ingestion: bool = False
    enable_live_wheelscreener: bool = False
    enable_live_kavout: bool = False
    enable_live_sterling: bool = False
    enable_live_market_data: bool = False


@dataclass
class SafetyConfig:
    no_auto_trading: bool = True
    discord_only_trade_allowed: bool = False
    require_multi_source_confirmation: bool = True
    require_manual_approval_for_options: bool = True
    block_wash_sale_candidates: bool = True
    block_wealthfront_overlap_etfs_in_robinhood: bool = True


@dataclass
class AppConfig:
    feature_flags: FeatureFlags = field(default_factory=FeatureFlags)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
