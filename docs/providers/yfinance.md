# yfinance

Used as our primary equity-data and FX source via OpenBB
(`obb.equity.*(provider="yfinance")`, `obb.currency.price.historical(provider="yfinance")`).

## What we trust yfinance for

- Current price (`equity.price.quote.last_price`)
- Market cap, shares outstanding (`equity.profile.market_cap`,
  `shares_outstanding`)
- Beta (regression beta as Yahoo computes it)
- Sector and industry classification (`sector`, `industry_category` —
  `industry` and `industry_group` are usually `None` via yfinance)
- Dividend yield
- ~4 years of annual income statement / balance sheet / cash flow
- Long business summary (a paragraph)
- FX rates for major currency pairs (EURUSD, GBPUSD, etc.)

## What we do NOT trust yfinance for

- **Authoritative GAAP fundamentals** — yfinance pulls from Yahoo's
  normalized data, which has its own provenance chain. Restatements and
  one-offs may be missing or inconsistent. **Always sanity-check against
  the actual annual report PDF** when a number looks off; raw OpenBB
  outputs are preserved in `./data/<TICKER_DIR>/raw/` for verification.
- **Long-history time series** — yfinance fundamentals return ~4 years;
  deeper history isn't available.
- **Segment-level data** — incomplete for many companies.
- **Fiscal calendar metadata** — `fiscal_year` and `fiscal_period` come
  back as `None` via OpenBB→yfinance. We derive `fiscalYear` from the
  `period_ending` date.
- **US 10-K MD&A or risk factors** — these come from EDGAR, which is out
  of scope for this fork.
- **PE ratio via quote** — `equity.price.quote.pe_ratio` is `null` for
  many tickers via yfinance. `summary.json.tradingMultiples.peRatio` will
  be `null` in those cases.

## Global ticker conventions

Yahoo uses suffixes for non-US exchanges. Examples:

| Region   | Suffix | Example      |
|----------|--------|--------------|
| US       | (none) | `AAPL`       |
| UK (LSE) | `.L`   | `BARC.L`     |
| France   | `.PA`  | `MC.PA`      |
| Germany  | `.DE`  | `SAP.DE`     |
| Japan    | `.T`   | `7203.T`     |
| Hong Kong| `.HK`  | `0700.HK`    |
| Australia| `.AX`  | `BHP.AX`     |
| India NSE| `.NS`  | `RELIANCE.NS`|

`tools/tickers.py:REGION_BY_SUFFIX` is the full mapping.

## TOS gray zone

The `yfinance` Python library is MIT-licensed open-source software, but
the underlying Yahoo Finance data it scrapes is TOS-restricted. This fork
uses yfinance as a documented exception to its "open data only" stance —
acceptable for personal/learning use; **not** suitable for commercial
redistribution. Surfaced in the README.

## When yfinance breaks

Yahoo periodically changes its endpoints, breaking yfinance scrapes.
Maintainers usually publish a fix within days. If `obb.equity.*(provider="yfinance")`
calls fail unexpectedly:

1. Upgrade: `pip install --upgrade yfinance openbb-yfinance`
2. Check the [yfinance issue tracker](https://github.com/ranaroussi/yfinance/issues).
3. As a temporary workaround, the OpenBB `tiingo` or `fmp` sub-providers
   may cover some equity data — but they require API keys and have
   different field shapes that would require `tools/normalize.py`
   adjustments. Not recommended unless the outage persists.
