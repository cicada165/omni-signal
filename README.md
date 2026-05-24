# omni-signal

Prototype investment-signal workspace.

## FMP Analyst Radar Prototype

This branch adds a lightweight Financial Modeling Prep analyst-radar prototype for tracking early professional-market belief changes around semiconductor, memory/HBM, AI infrastructure, and related themes.

It uses FMP as a structured analyst/trend source, then produces local JSON and Markdown digests. The key is intentionally read from `FMP_API_KEY`; do not commit API keys.

FMP endpoints used in the first prototype:

- `price-target-consensus`
- `price-target-summary`
- `analyst-estimates`
- `ratings-snapshot`

This is not investment advice. It is an analyst-signal monitoring digest.

## Purpose

The goal is to generate a compact, reviewable digest that helps surface changing expectations across a small watchlist. The prototype is intentionally call-budget aware and designed for the free FMP tier first.

## Setup

1. Export your FMP key into the environment:

```bash
export FMP_API_KEY="your_key_here"
```

2. Do not commit the key into files, logs, snapshots, or generated digest outputs.
3. Run from the repo root with `PYTHONPATH=src`.

## Dry Run

Validate the watchlist, deduplicate tickers, and estimate call volume without calling FMP:

```bash
PYTHONPATH=src python3 scripts/run_fmp_analyst_radar.py \
  --watchlist config/watchlists/semiconductor_themes.json \
  --output-dir data/digests \
  --dry-run
```

## Live Smoke Test

Run a small live sample after exporting `FMP_API_KEY`:

```bash
PYTHONPATH=src python3 scripts/run_fmp_analyst_radar.py \
  --watchlist config/watchlists/semiconductor_themes.json \
  --output-dir data/digests \
  --max-tickers 3
```

You can also narrow the run:

```bash
PYTHONPATH=src python3 scripts/run_fmp_analyst_radar.py \
  --watchlist config/watchlists/semiconductor_themes.json \
  --output-dir data/digests \
  --tickers NVDA,AMD,MU
```

## Tests

Run the unit test suite:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test*.py'
```

## Free-Tier Limits

The CLI estimates calls before fetching data:

- `unique_tickers * enabled_endpoints`
- warn above 200 planned calls
- require `--force` above 250 planned calls

The prototype keeps the endpoint list intentionally small:

- price target consensus
- price target summary
- analyst estimates
- ratings snapshot

## Output

The CLI writes local digest files under `data/digests/`:

- `latest.json`
- `latest.md`

These are generated artifacts and should not be committed.

## Analyst Use

FMP is used here as a structured input source for trend monitoring and review. It is not the final decision engine. Use the digest as one input among fundamentals, valuation, risk management, and your own thesis.
