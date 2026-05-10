# Data conventions

This fork uses a **pre-fetched local cache** of open-source financial data.
No MCP servers are configured. Do not attempt to call MCPs.
Do not use web search for fundamental data.

## Where data lives

Per-ticker cache: `./data/<TICKER_DIR>/`
- `summary.json` — canonical contract; READ THIS FIRST
- `raw/` — vendor-native files for verification or fields missing from summary

Shared (not ticker-scoped): `./data/_shared/`
- `rates/` — risk-free rate series by country (US/UK/EU/JP)
- `fx/` — yfinance FX rates (USD per unit of major currencies)
- `macro/` — OECD GDP and CPI series

## Ticker directory naming

Yahoo suffixes use periods (e.g. `7203.T`, `BARC.L`). Directory names
replace periods with underscores (`7203_T`, `BARC_L`). The original ticker
is preserved in `summary.json.ticker`.

## Workflow

1. Skill needs data for ticker `<T>`.
2. Read `./data/<T_DIR>/summary.json`. Use values; cite each via the `source` field.
3. If a field you need isn't in `summary.json`, look in `./data/<T_DIR>/raw/`.
4. If `summary.json` is missing OR `fetched_at.txt` is older than 24h, STOP.
   Tell the user: "Run `python tools/fetch.py <TICKER>` to populate the cache."

## Source citations

Every numeric field in `summary.json` carries a `source` string. Use it
**verbatim** in cell comments — do not paraphrase, do not abbreviate.

## Cross-currency analysis

For comp sets or models spanning multiple currencies, use FX rates from
`./data/_shared/fx/yfinance_fx.csv`. Rates are USD-per-unit (1 EUR ≈ 1.18 USD,
1 JPY ≈ 0.0064 USD). Convert non-USD figures to USD by multiplying by the
appropriate rate.

## What this fork does NOT cover (acknowledge in user-facing output)

- US 10-K/10-Q filings (EDGAR is out of scope)
- Transaction comps / M&A precedents
- Analyst consensus estimates
- Real-time / intraday prices
- Auto-suggested peers (requires FMP API key; specify peers manually via
  `--peers` flag instead)
- `/lbo` command (not patched for this data layer; will likely fail)
