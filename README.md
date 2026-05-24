# omni-signal

Prototype investment-signal workspace.

## FMP analyst radar prototype

This branch adds a lightweight Financial Modeling Prep analyst-radar prototype for tracking early professional-market belief changes around semiconductor, memory/HBM, AI infrastructure, and related themes.

It uses FMP as a structured analyst/trend source, then produces local JSON and Markdown digests. The key is intentionally read from `FMP_API_KEY`; do not commit API keys.

FMP endpoints used in the first prototype:

- `price-target-consensus`
- `price-target-summary`
- `analyst-estimates`
- `ratings-snapshot`

## Run tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test*.py'
```

## Run a live free-tier smoke test

```bash
export FMP_API_KEY="your_key_here"
PYTHONPATH=src python scripts/run_fmp_analyst_radar.py \
  --watchlist config/watchlists/semiconductor_themes.json \
  --output-dir data/digests
```

Generated digests are ignored by git under `data/digests/`.

## Free-tier call budget

The default watchlist currently contains duplicated tickers across themes. The prototype intentionally preserves theme membership for analysis, but the next iteration should deduplicate live calls per ticker before scoring each theme. Keep the free-tier test small and prefer daily/weekly digest cadence over frequent polling.
