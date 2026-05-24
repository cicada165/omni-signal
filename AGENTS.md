# Codex guidance for omni-signal

## Prototype scope

The current branch contains a small FMP analyst-radar prototype. The goal is to detect early market theme shifts from analyst-derived data rather than scraping websites or asking an agent to infer signals from raw filings, news, or prices.

## Guardrails

- Never commit API keys, CSV exports with account data, brokerage statements, or generated digest artifacts.
- Read the FMP key from `FMP_API_KEY` only.
- Keep the free-tier test small enough to stay under 250 calls/day.
- Treat FMP as an input signal, not as investment advice or an automated trading trigger.
- Prefer deterministic scoring and explainable digest output before adding LLM summarization.
- Use `--summary-only` for a lower-cost run when you only need price-target context.
- Use `--cache-dir` for repeat live runs so previously fetched JSON responses can be reused locally.

## Current test command

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test*.py'
```

## Manual live smoke test

```bash
export FMP_API_KEY="..."
PYTHONPATH=src python3 scripts/run_fmp_analyst_radar.py \
  --watchlist config/watchlists/semiconductor_themes.json \
  --output-dir data/digests
```
