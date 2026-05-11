# altree-finance — Project handoff

**Repo:** https://github.com/wangzaa/altree-finance
**Owner:** andrew@altree.co
**Status as of:** 2026-05-11
**Latest tag:** `v0.1.0` (initial release); subsequent fixes on `main`

This document captures purpose, architecture, and the issue log accumulated
during initial build and the first two stock analyses (CATL `3750.HK`,
Rheinmetall `RHM.DE`). It exists so future-you (or anyone picking this up)
can get to productive use without re-deriving decisions from commit history.

---

## 1. Purpose & objectives

### Purpose

A personal-use fork of [`anthropics/financial-services`](https://github.com/anthropics/financial-services)'s
`financial-analysis` plugin, with the **11 paid/enterprise MCP data sources
replaced by open-source data via OpenBB Platform**. Global ticker coverage,
not US-only.

### Objectives

1. **`/dcf`, `/comps`, `/3-statement-model`, `/competitive-analysis` run end-to-end** against any covered global equity ticker, sourcing all numeric inputs from a local cache. No paid MCPs, no fundamental web search.
2. **Audit-trail is non-negotiable.** Every numeric field in `summary.json` carries a `source` string used verbatim in Excel cell comments.
3. **Reproducible.** Same cache snapshot → same model. Cache is hybrid (raw vendor files + normalized `summary.json`).
4. **Global by default.** US, UK, Eurozone, non-Eurozone DM Europe, Japan, Asia DM, Asia EM, Americas non-US, other EM.
5. **Country-specific tax** where it materially matters (Germany 30%, Ireland 12.5%, Hong Kong 16.5%, Brazil 34%, etc.). Regional defaults for ERP and country risk premium.
6. **Light layered fork.** Data policy centralized in two convention docs (`DATA_CONVENTIONS.md`, `FORMATTING_CONVENTIONS.md`) that all skills defer to. Upstream skill rebases stay clean.
7. **Per-project working directories.** Each analysis is its own dir with copied `tools/` and `data/`. Snapshot-able, no cross-contamination.

### What this project is NOT

- Not a paid-data replacement at institutional quality. Retail-grade fundamentals via yfinance, ~4 years history vs. EDGAR's 10+.
- Not a real-time / intraday system. EOD only.
- Not suitable for commercial redistribution. yfinance is OSS but Yahoo's data is TOS-restricted; documented exception for personal use.
- Not covering `/lbo` (transaction-comp data has no open source).
- Not covering EDGAR 10-K MD&A; `/competitive-analysis` is meaningfully thinner than upstream.

---

## 2. Data flow & architecture

### High-level flow

```
┌────────────────────────────────────────────────────────────────┐
│ Claude Code session in ~/work/<project>/                       │
│   loads plugin "altree-finance"                                │
│   ─ /dcf, /comps, /3-statement-model, /competitive-analysis    │
└────────────────────────────────────────────────────────────────┘
                              │ reads
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ Skills (in plugin/skills/, lightly patched from upstream)      │
│   defer to:                                                    │
│   ─ DATA_CONVENTIONS.md     (where to read data)               │
│   ─ FORMATTING_CONVENTIONS.md (Arial 10pt, overflow rules)     │
└────────────────────────────────────────────────────────────────┘
                              │ reads
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ Per-project cache  ./data/                                     │
│   ─ <TICKER_DIR>/summary.json   (canonical contract)           │
│   ─ <TICKER_DIR>/raw/           (OpenBB raw outputs)           │
│   ─ _shared/rates/              (US/UK/EU/JP 10Y)              │
│   ─ _shared/fx/                 (EUR/GBP/JPY/AUD/CAD/CHF/USD)  │
│   ─ _shared/macro/              (OECD GDP, CPI)                │
└────────────────────────────────────────────────────────────────┘
                              │ written by
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ Per-project tools/  (5 Python files, ~600 LOC total)           │
│   ─ tickers.py    region + dir-name from Yahoo suffix          │
│   ─ defaults.py   ERP/CRP regional, tax country-specific       │
│   ─ normalize.py  OpenBB raw → summary.json                    │
│   ─ shared.py     _shared/ cache refresh                       │
│   ─ fetch.py      CLI orchestrator                             │
└────────────────────────────────────────────────────────────────┘
                              │ wraps
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ OpenBB Platform 4.7.x (MIT, open source software)              │
│   Sub-providers we use (all key-free, open-data):              │
│   ─ yfinance         equity profile / quote / fundamentals     │
│                      + FX (currency.price.historical)          │
│   ─ federal_reserve  US Treasury 10Y (H.15)                    │
│   ─ econdb           UK / Japan / global rates;                │
│                      ECB spot rate for Eurozone                │
│   ─ oecd             GDP, CPI for major countries              │
└────────────────────────────────────────────────────────────────┘
```

### Repo layout

```
altree-finance/
├── HANDOFF.md                      ← this document
├── README.md                       user-facing setup
├── LICENSE                         Apache 2.0 (matches upstream)
├── NOTICE                          attribution
├── requirements.txt                Python deps for tools/
├── requirements-dev.txt            pytest
├── .gitignore
├── .claude-plugin/
│   └── marketplace.json            single-plugin marketplace metadata
├── plugin/                         ← the actual Claude Code plugin
│   ├── .claude-plugin/plugin.json
│   ├── .mcp.json                   empty (no MCPs)
│   ├── DATA_CONVENTIONS.md         data policy (where summary.json lives)
│   ├── FORMATTING_CONVENTIONS.md   Excel formatting (Arial 10pt, overflow)
│   ├── commands/                   patched: dcf, comps, 3-statement, competitive
│   ├── skills/                     patched: dcf-model, comps-analysis,
│   │                               3-statement-model, competitive-analysis,
│   │                               xlsx-author; rest unchanged
│   └── hooks/                      unchanged from upstream
├── tools/                          Python data layer (copy into each project)
│   ├── tickers.py
│   ├── defaults.py
│   ├── normalize.py
│   ├── shared.py
│   └── fetch.py
├── tests/                          61 pytest tests
│   ├── conftest.py
│   ├── fixtures/                   OpenBB-shaped JSON
│   ├── test_tickers.py             20+ region/suffix tests
│   ├── test_defaults.py            country-specific tax tests
│   └── test_normalize.py           build_summary fixture tests
└── docs/
    ├── data-schema.md              summary.json contract
    ├── providers/openbb.md         OpenBB sub-provider notes
    ├── providers/yfinance.md       caveats; full suffix→region table
    └── adding-a-provider.md        contributor recipe
```

### Per-analysis lifecycle

```bash
# One-time per analysis
mkdir -p ~/work/<project> && cd ~/work/<project>
cp -r ~/code/altree-finance/tools .
cp ~/code/altree-finance/requirements.txt .
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Data fetch (peers comma-separated; --tax-rate applies to primary only)
python tools/fetch.py <TICKER> --peers PEER1,PEER2,... [--tax-rate 0.30]

# In Claude Code, with working dir = ~/work/<project>:
/comps <TICKER> --peers PEER1,PEER2,...
/dcf <TICKER>
# Output: ./out/<model>.xlsx in Arial 10pt
```

### summary.json contract (excerpt — see `docs/data-schema.md` for full schema)

```jsonc
{
  "ticker": "RHM.DE", "directoryName": "RHM_DE", "region": "EUROZONE",
  "asOf": "2026-05-11", "fetchedAt": "2026-05-11T...Z",
  "company": { "name", "sector", "industry", "description_short", ... },
  "marketData": {
    "currency": "EUR", "price", "marketCap", "sharesOutstanding",
    "beta_yfinance", "dividendYield",
    "source": "yfinance via OpenBB 2026-05-11"
  },
  "incomeStatement": { "currency", "periods": [/* up to ~4y */] },
  "balanceSheet":    { "currency", "periods": [...] },
  "cashFlow":        { "currency", "periods": [...] },
  "wacc_inputs": {
    "riskFreeRate":      { "value": 0.0365, "source": "OpenBB econdb ECB spot 10Y 2025-04-11" },
    "equityRiskPremium": { "value": 0.0550, "source": "tools/defaults.py EUROZONE default" },
    "countryRiskPremium":{ "value": 0.0000, "source": "tools/defaults.py EUROZONE default" },
    "industryBeta": null,
    "marginalTaxRate": 0.30   // country-specific from MARGINAL_TAX_BY_SUFFIX[".DE"]
  },
  "tradingMultiples": { "ev", "evToRevenue_LTM", "evToEbitda_LTM", "peRatio", ... },
  "peers": { "suggested_yfinance": [], "selected": ["BA.L", "LDO.MI", ...] },
  "fx": { "reportingCurrency", "ratesToUSD", "ratesToEUR" }
}
```

### Region + tax resolution

- **Region** keyed by Yahoo suffix in `tools/tickers.py:REGION_BY_SUFFIX` (~50 suffixes covering most global markets). Drives ERP and CRP defaults.
- **Marginal tax** keyed by Yahoo suffix in `tools/defaults.py:MARGINAL_TAX_BY_SUFFIX` (~40 country entries). Country-specific values from OECD/national tax data.
- **Risk-free rate** resolved by region → file lookup in `tools/fetch.py:_rate_csv_for`:
  - US → `_shared/rates/us_10y.csv` (federal_reserve provider)
  - UK → `_shared/rates/uk_10y.csv` (econdb)
  - EUROZONE → `_shared/rates/eu_10y.csv` (econdb ecb_spot_rate)
  - JAPAN → `_shared/rates/jp_10y.csv` (econdb)
  - ASIA_DM / ASIA_EM / OTHER → falls back to `us_10y.csv` (known limitation; see §3)

### Three convention documents

Skills defer to these instead of carrying policy inline. Keeps the fork rebase-friendly.

1. **`plugin/DATA_CONVENTIONS.md`** — where data lives, the workflow, source citation rules, cross-currency policy, currency idiosyncrasy log.
2. **`plugin/FORMATTING_CONVENTIONS.md`** — Arial 10pt mandate, blue/black/green palette, Notes & Methodology overflow rules + required content.
3. **`docs/data-schema.md`** — formal `summary.json` schema with field-level rules.

---

## 3. Issue log to date

### Issues discovered during build & resolved

| # | Issue | Resolution | Commit |
|---|---|---|---|
| 1 | Upstream plugin used `"source": "."` in marketplace.json; Claude Code rejected as "source type not supported" | Restructured to put plugin contents in `plugin/` subdir; marketplace points to `./plugin` | `5cadbcf` |
| 2 | Initial normalize.py used yfinance Python library schema (`longName`, `marketCap`, etc.); OpenBB returns its own snake_case schema | Rewrote normalize.py against OpenBB schema with fixture-driven tests | `5a8ed8f` |
| 3 | `equity.profile` returns `industry: None` via yfinance; human-readable industry is in `industry_category` | Fall back across `industry → industry_group → industry_category` | (in #2 commit) |
| 4 | `equity.fundamental.*` returns `fiscal_year: None` and `fiscal_period: None` via yfinance | Derive `fiscalYear` from YYYY prefix of `period_ending` date in normalize.py | (in #2 commit) |
| 5 | Plan assumed direct ECB/BoE/BoJ providers for `yield_curve`; only `federal_reserve`, `econdb`, `fmp`, `fred` available | Use `econdb` with country code for non-US; `ecb_spot_rate` for Eurozone | `a341217` |
| 6 | `currency.price.historical` has no ECB provider (only `fmp`, `tiingo`, `yfinance`) | Use `yfinance` for FX pairs (EUR/GBP/JPY/AUD/CAD/CHF=X) — consistent with rest of equity data | `a341217` |
| 7 | `equity.compare.peers` requires FMP API key (commercial) | Disable auto-suggestion; require `--peers` flag for manual peer selection | (in fetch.py) |
| 8 | `python tools/fetch.py` failed with `ModuleNotFoundError: No module named 'tools'` | Added `sys.path` injection at top of fetch.py so it works as a script | `2c52e16` |
| 9 | `tools/tickers.py` REGION_BY_SUFFIX only covered ~13 suffixes (US, UK, parts of Eurozone, JP, basic Asia) | Expanded to ~50 suffixes: China (`.SZ`, `.SS`), Korea (`.KS`, `.KQ`), Taiwan, NZ, Nordics, Americas non-US, smaller EM | `fcb5d2c` |
| 10 | Skills' default font (Calibri 11pt) and comps' "Suggested" Times New Roman were inconsistent | Mandated **Arial 10pt** across all Excel outputs via `FORMATTING_CONVENTIONS.md`; patched xlsx-author, comps, dcf, 3-statement to reference it | `0dcc05d` |
| 11 | Marginal tax rate was regional bucket (EUROZONE = 25%) — wrong for Germany (30%), Ireland (12.5%), etc. | Added `MARGINAL_TAX_BY_SUFFIX` country-level dict; `get_defaults(region, suffix)` prefers country over region for tax | `c22c736` |
| 12 | `fetch.py --tax-rate 0.30` applied 30% to every ticker including peers (wrong for BA.L UK = 25%) | Scoped CLI overrides to primary ticker only (`is_primary = tkr == args.ticker`) | `c22c736` |
| 13 | Comp tables risked silent cross-currency conversion errors (BA.L pence vs GBP, missing SEK/NOK FX) | Mandated **multiples-only** policy for `/comps`; absolutes shown in each company's own reporting currency in supporting tabs only | `c6a6472` |
| 14 | Notes & Methodology text wrapping inflated row heights inconsistently | Mandated `wrap_text=False` (overflow, not wrap) for Notes & Methodology cells | `c6a6472` |
| 15 | Auto-peer-suggestion warning surfaced as confusing output during fetch | Documented in suggest-peers flow that users must specify `--peers` manually; not a bug, just an explicit limitation | (docs/providers/openbb.md) |

### Known limitations (NOT bugs; design constraints accepted)

#### Data quality and coverage

- **Fundamentals depth ≈ 4 years.** yfinance provides ~4 years of annual history via OpenBB. Long-horizon trend analysis degrades. EDGAR offered 10+; out of scope here.
- **No filings narrative.** Dropping EDGAR removes 10-K MD&A, risk factors, segment commentary. `/competitive-analysis` runs on yfinance's `long_description` (paragraph) + Wikipedia (best-effort).
- **Fundamentals are derived, not authoritative.** yfinance pulls from Yahoo's normalized data with its own provenance chain. Restatements, one-offs, segment splits sometimes missing or inconsistent. Always sanity-check against the actual annual report PDF when a number looks off; raw OpenBB outputs in `./data/<TICKER>/raw/` are preserved.
- **Beta is noisy.** yfinance regression beta only — no Damodaran industry beta. Sensitivity tables compensate.

#### Regional / country gaps

- **ASIA_DM and ASIA_EM risk-free rates fall back to US 10Y.** No econdb provider for HK/SG/AU/IN-specific 10Y bonds in OpenBB 4.7.1. HKD pegged to USD makes this defensible for HK; less so for INR/AUD/SGD analyses. Source string says "OpenBB econdb regional 10Y" but the actual CSV is `us_10y.csv`.
- **Non-Eurozone DM Europe mapped to EUROZONE region** for ERP / CRP. Swiss tax materially lower (~14-21% by canton vs EUROZONE 25%); country-specific tax (`.SW = 18%`) helps but doesn't perfectly model cantonal variation.
- **China A-shares**: yfinance coverage of `.SS` and `.SZ` is patchy. Multiples often work; fundamentals depth varies by ticker.
- **Smaller European exchanges**: Nordic exchanges (`.OL`, `.ST`, `.CO`, `.HE`) covered but yfinance fundamentals can be sparse.
- **Some recent IPOs**: e.g., R3NK.DE (Renk, Feb 2024 IPO) has only 1-2 years of fundamentals.

#### Currency idiosyncrasies (must surface in Notes & Methodology of every model that uses these tickers)

- **`BA.L` (BAE Systems)**: `summary.json.marketData.currency` is `"GBp"` (pence) but `marketCap` is denominated in **GBP**, NOT pence. Do not multiply market cap by 100. yfinance/Yahoo quirk.
- **`SAAB-B.ST` (SEK)** and **`KOG.OL` (NOK)**: reporting currencies absent from `_shared/fx/yfinance_fx.csv` (which covers EUR/GBP/JPY/AUD/CAD/CHF only). Stick to multiples-only when including these; do not attempt SEK/NOK conversion without extending `tools/shared.py:FX_PAIRS` first.
- **All UK LSE tickers**: many report price in pence. Check `marketData.currency` for each before any conversion.

#### Open-source-purity caveats

- **yfinance is TOS-gray.** Library is MIT-licensed but underlying Yahoo data is TOS-restricted. Acceptable for personal/learning use; not suitable for commercial redistribution. Surfaced in README and NOTICE.
- **ERP regional defaults are stale by construction.** Annual review burden (typically against Damodaran's published series each January).
- **Country tax rates stale by construction.** Annual review against OECD statutory rate data.
- **Some econdb rate dates are stale** (e.g., EU 10Y last refresh shows 2025-04-11). Newer yields require manual override in the model.

#### Out of scope by design

- `/lbo` command — transaction-comp data has no open source.
- Real-time / intraday data — yfinance/OpenBB are EOD.
- M&A precedent transactions.
- Analyst consensus estimates (yfinance has some but spotty for non-US).
- Earnings call transcripts at depth (commercial-only).
- Auto-peer-suggestion (requires FMP API key; use `--peers` flag instead).

### Maintenance burden you're signing up for

- **OpenBB version churn**: updates frequently with occasional breaking changes. Pinned `openbb>=4.4,<5.0` in `requirements.txt`. Upgrade deliberately.
- **yfinance Yahoo-scrape breaks**: Yahoo periodically changes endpoints; yfinance maintainers usually patch within days.
- **Annual ERP / CRP / tax table refresh**: ~30 min once a year against Damodaran + OECD.
- **Upstream plugin rebases**: when Anthropic updates `financial-services`. Light-fork structure keeps merge surface small.

### Open follow-ups (nice-to-have, not urgent)

- Add SEK and NOK to `tools/shared.py:FX_PAIRS` so Nordic peer sets can do absolute-figure conversion if ever needed (currently locked out of that by multiples-only policy anyway).
- Add ASIA_DM and ASIA_EM specific rate files (Hong Kong 10Y, India 10Y, etc.) so the risk-free fallback to US 10Y is no longer needed.
- Add an `industryBeta` source — possibly Damodaran's annual unlevered beta tables (free, but require manual download and parsing).
- Consider a `verify.py` script that opens a generated `.xlsx`, walks every blue input cell, and checks its comment matches a `source` string in `summary.json`. Audit tool, not a blocker.
- Bump `.claude-plugin/plugin.json` version on each meaningful change; currently still `0.1.0` even though `main` has diverged. Tag `v0.2.0` when there's a coherent next milestone.

---

## Quick start (for someone picking this up)

```bash
# Clone
git clone git@github.com:wangzaa/altree-finance.git ~/code/altree-finance
cd ~/code/altree-finance

# Install plugin in Claude Code (one time)
claude plugin marketplace add ~/code/altree-finance
claude plugin install altree-finance@altree-finance

# Set up a new analysis
mkdir -p ~/work/<my-analysis> && cd ~/work/<my-analysis>
cp -r ~/code/altree-finance/tools .
cp ~/code/altree-finance/requirements.txt .
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Fetch
python tools/fetch.py <TICKER> --peers PEER1,PEER2,...

# In a Claude Code session with cwd = ~/work/<my-analysis>:
#   /comps <TICKER> --peers PEER1,PEER2,...
#   /dcf <TICKER>
```

Read `README.md` for user-facing setup, `plugin/DATA_CONVENTIONS.md` for the
data contract, `plugin/FORMATTING_CONVENTIONS.md` for Excel output rules,
and `docs/data-schema.md` for the full `summary.json` schema.
