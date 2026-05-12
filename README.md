# Omni Signal

Omni Signal is a **read-only signal evaluation harness** for ingesting and scoring trading signals from exports and datasets.

## What Omni Signal does
- Ingests offline exports from Discord JSON, WheelScreener CSV (future), Kavout CSV, Sterling CSV, portfolio CSV, and market-data snapshots.
- Normalizes signal formats into a common typed model.
- Scores signals with conservative multi-source boosts.
- Applies safety/risk blocking rules.
- Generates markdown reports and a Streamlit dashboard view.

## What Omni Signal does NOT do
- No broker integrations.
- No live order placement or execution.
- No Robinhood stock/options trading APIs.
- No auto-trading mode.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## Example offline workflow
```bash
omni-signal init-db
omni-signal ingest-examples
omni-signal score
omni-signal report --out reports/daily.md
streamlit run omni_signal/dashboard/streamlit_app.py
```

## Required API keys for future live integrations
Future optional integrations may require:
- `WHEELSCREENER_API_KEY`
- `KAVOUT_API_KEY`
- `DISCORD_BOT_TOKEN`
- `DISCORD_CHANNEL_ID`
- `MARKET_DATA_PROVIDER`
- `DATABASE_URL`

All live integration feature flags default to disabled.

## Safety and risk disclaimers
This project is for research/evaluation only, not investment advice. Keep offline mode as default, review all outputs manually, and never auto-execute trades from model output.
