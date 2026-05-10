---
description: Create a competitive landscape analysis
argument-hint: "[company or industry]"
---

**Pre-flight (this fork uses a local cache):** If a specific company is
the target, verify `./data/<TICKER_DIR>/summary.json` exists and
`fetched_at.txt` is < 24h old. If missing or stale, instruct the user to
run `python tools/fetch.py <TICKER>` (and the same for any named peers
via `--peers`) and stop until they confirm. See `DATA_CONVENTIONS.md` for
full data-policy details.

---

Load the `competitive-analysis` skill and build a competitive landscape analysis for the specified company or industry.

If a company/industry is provided as an argument, use it. Otherwise ask the user what they want to analyze.
