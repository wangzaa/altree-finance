---
description: Fill out a 3-statement financial model template
argument-hint: "[path to template file]"
---

**Pre-flight (this fork uses a local cache):** If the template will be
populated against a specific company's historicals, verify
`./data/<TICKER_DIR>/summary.json` exists and `fetched_at.txt` is < 24h
old. If missing or stale, instruct the user to run
`python tools/fetch.py <TICKER>` and stop until they confirm. See
`DATA_CONVENTIONS.md` for full data-policy details.

---

Load the `3-statement-model` skill and populate a 3-statement financial model (Income Statement, Balance Sheet, Cash Flow Statement).

If a file path is provided, use it as the template. Otherwise ask the user for their model template.
