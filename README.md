# altree-finance

An open-source-data fork of [`anthropics/financial-services`](https://github.com/anthropics/financial-services)'s `financial-analysis` plugin.

## What this fork is

The upstream plugin builds DCFs, comps, 3-statement models, and competitive analyses
using **11 paid/enterprise MCP data sources** (Daloopa, Morningstar, S&P Kensho,
FactSet, Moody's, MT Newswires, Aiera, LSEG, PitchBook, Chronograph, Egnyte).

**This fork drops all 11 paid MCPs and replaces them with a pre-fetched local cache
sourced from open-source data:**

| Need                                  | Source (open)                                  |
|---------------------------------------|------------------------------------------------|
| Equity prices, market data, key stats | OpenBB → yfinance                              |
| Fundamentals (~4 yrs IS/BS/CF)        | OpenBB → yfinance                              |
| Risk-free rate (US 10Y)               | OpenBB → Federal Reserve H.15                  |
| Risk-free rates (UK/EU/JP 10Y)        | OpenBB → econdb (UK gilt, ECB spot, JGB)       |
| FX rates                              | OpenBB → yfinance (EUR/GBP/JPY/AUD/CAD/CHF)    |
| Macro (GDP, CPI)                      | OpenBB → OECD                                  |
| Equity risk premium                   | Hardcoded regional defaults (`tools/defaults.py`) |
| Company narrative                     | yfinance summary + Wikipedia (best-effort)     |

## What this fork covers

| Command                  | Status                                       |
|--------------------------|----------------------------------------------|
| `/dcf`                   | Patched — uses local cache                   |
| `/comps`                 | Patched                                      |
| `/3-statement-model`     | Patched                                      |
| `/competitive-analysis`  | Patched                                      |
| `/lbo`                   | Not patched — will fail without paid MCPs    |
| `/debug-model`           | Unchanged from upstream                      |
| `/ppt-template`          | Unchanged from upstream                      |

## Setup

### 1. Install the plugin

Local install (recommended while iterating):

Add to `~/.claude/settings.json`:
```json
{
  "extraKnownMarketplaces": {
    "altree-finance-local": {
      "source": {"source":"local","path":"/Users/<you>/code/altree-finance"}
    }
  }
}
```

Then:
```bash
claude plugin install altree-finance@altree-finance-local
```

Or install from GitHub once pushed:
```bash
claude plugin install altree-finance@wangzaa/altree-finance
```

### 2. Set up a project directory

For each financial-analysis project, create a working dir and copy the tools:

```bash
mkdir -p ~/work/aapl-valuation && cd $_
cp -r ~/code/altree-finance/tools .
cp ~/code/altree-finance/requirements.txt .
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Fetch data for a ticker

```bash
python tools/fetch.py AAPL                          # US
python tools/fetch.py 7203.T                        # Japan (Toyota)
python tools/fetch.py BARC.L                        # UK (Barclays)
python tools/fetch.py 0700.HK                       # Hong Kong (Tencent)
python tools/fetch.py AAPL --peers MSFT,GOOG,DELL   # for /comps
```

This populates `./data/<TICKER_DIR>/summary.json` and `./data/_shared/`.

### 4. Run a skill in Claude Code

From the project working dir:

```
/dcf AAPL
/comps AAPL --peers MSFT,GOOG,DELL
/3-statement-model
/competitive-analysis AAPL
```

Skills read from `./data/<TICKER_DIR>/summary.json`. If the cache is missing
or stale (>24h), the skill will tell you to run `python tools/fetch.py` first.

## Known limitations

- **No 10-K/10-Q filings narrative** — EDGAR is out of scope. `/competitive-analysis`
  runs on yfinance's `long_description` plus Wikipedia.
- **Fundamentals depth ≈ 4 years** — yfinance provides ~4y history vs. EDGAR's 10+.
- **Beta is noisy** — yfinance's regression beta only.
- **ERP is a static regional default** — review `tools/defaults.py` annually
  (typically against Damodaran's published series in January).
- **Coverage gaps** — China A-shares, smaller European exchanges (Nordic/CEE),
  some emerging markets.
- **EOD only** — no real-time/intraday data.
- **Auto-peer-suggestion not available** — OpenBB's `equity.compare.peers`
  requires an FMP API key in 4.7.x. Specify peers manually via `--peers`.
- **yfinance is TOS-gray** — the underlying Yahoo Finance data is TOS-restricted
  even though the yfinance library is MIT-licensed. Acceptable for personal use;
  not suitable for commercial redistribution.

## Maintenance

- **OpenBB version churn**: pin in `requirements.txt`; upgrade deliberately.
- **yfinance Yahoo-scrape breaks**: usually patched within days by yfinance maintainers.
- **Annual ERP/CRP table refresh**: ~10 min once a year.
- **Upstream plugin rebases**: light-fork structure keeps merge surface small.

## Contributing

See [`docs/adding-a-provider.md`](docs/adding-a-provider.md) for how to wire a
new open-source data source into `tools/normalize.py`.

## License

Apache 2.0 (matching upstream). See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
