# OpenBB Platform

[OpenBB](https://docs.openbb.co/platform) is the spine of this fork's data
layer. MIT-licensed open-source software that wraps ~100 upstream data
sources behind a uniform Python API.

## Sub-providers we use (verified against OpenBB 4.7.1)

We deliberately use only OpenBB sub-providers that are key-free and
open-data:

| Sub-provider     | OpenBB call                                          | Used for                         |
|------------------|------------------------------------------------------|----------------------------------|
| `yfinance`       | `equity.profile`, `equity.price.quote`, `equity.fundamental.{income,balance,cash}` | Equity prices, fundamentals       |
| `yfinance`       | `currency.price.historical(symbol="EURUSD=X", ...)`  | FX rates (USD per major currency) |
| `federal_reserve`| `fixedincome.government.yield_curve`                 | US 10Y Treasury (H.15)           |
| `econdb`         | `fixedincome.government.yield_curve(country="...")`  | UK / EU / JP 10Y rates           |
| `oecd`           | `economy.gdp.real`, `economy.cpi`                    | GDP, CPI for major countries     |

Sub-providers requiring API keys (FMP, Polygon, Intrinio, Tiingo) are NOT
used and should NOT be enabled in this fork.

## Known API surface deviations from naive expectations

Several plan/spec assumptions did not match the actual OpenBB 4.7.1 API.
These deviations are baked into `tools/shared.py` and `tools/normalize.py`:

1. **`yield_curve` returns single-date snapshots, not time series.** Each
   row is a different maturity (1M, 3M, 6M, 1Y, ..., 10Y, 30Y) for the same
   date. We extract the row closest to `maturity_years == 10.0`.
2. **There is no direct ECB / BoE / BoJ provider** for `yield_curve`.
   Available providers: `econdb`, `federal_reserve`, `fmp`, `fred`. We use
   `econdb` for non-US (with `country='united_kingdom' | 'japan' | 'ecb_spot_rate'`).
3. **There is no direct ECB FX provider** in `currency.price.historical`.
   Available providers: `fmp`, `tiingo`, `yfinance`. We use `yfinance`
   (consistent with the rest of the equity-data stack).
4. **`equity.compare.peers` requires `provider='fmp'`** which needs an API
   key. Without a key, peer suggestion is unavailable; users specify peers
   via `--peers TICKER1,TICKER2,...`.
5. **`equity.profile` returns `industry: None` for many tickers via
   yfinance.** The human-readable industry is in `industry_category`.
   `normalize.py` falls back across `industry → industry_group →
   industry_category`.
6. **`equity.fundamental.*` returns `fiscal_year: None` and
   `fiscal_period: None`** when the underlying source is yfinance.
   `normalize.py` derives `fiscalYear` from the YYYY prefix of
   `period_ending`.
7. **Field name reality check** — OpenBB uses snake_case throughout, and
   diverges from yfinance Python library names:
   - profile: `name` (not `longName`), `market_cap` (not `marketCap`),
     `shares_outstanding` (not `sharesOutstanding`),
     `dividend_yield` (not `dividendYield`),
     `long_description` (not `longBusinessSummary`)
   - balance: `total_liabilities_net_minority_interest` (not
     `total_liabilities`), `total_common_equity` (not `total_equity`),
     `cash_and_cash_equivalents` (not `cash_and_equivalents`)
   - cash: `capital_expenditure` (singular, not `capital_expenditures`)

## Version pinning

`requirements.txt` pins `openbb>=4.4,<5.0`. OpenBB ships breaking changes
between major versions; bump the pin only after re-running the smoke tests
in this repo's `tools/shared.py` and `tools/fetch.py`.

## When OpenBB API calls break

If a call in `tools/shared.py` or `tools/fetch.py` raises an `AttributeError`
or unexpected schema, check:

1. The OpenBB release notes for the version installed in your venv.
2. `https://docs.openbb.co/platform/reference` for the current call surface.
3. Re-probe the API:
   ```python
   from openbb import obb
   import inspect
   print(inspect.signature(obb.fixedincome.government.yield_curve))
   ```
4. Update the affected lines in `tools/shared.py` / `tools/fetch.py` and
   note the change in your fork's commit message.
