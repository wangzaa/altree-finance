# `summary.json` schema

The canonical per-ticker contract. Skills read this first; raw vendor files
in `raw/` are fallback. Every numeric field that has an external source
carries a sibling `source` string used verbatim in cell comments.

```json
{
  "ticker":         "AAPL",
  "directoryName":  "AAPL",
  "region":         "US",
  "asOf":           "2026-05-10",
  "fetchedAt":      "2026-05-10T14:32:00Z",

  "company": {
    "name":              "Apple Inc.",
    "sector":            "Technology",
    "industry":          "Consumer Electronics",
    "description_short": "Apple Inc. designs, ...",
    "narrative_path":    "raw/wikipedia_summary.json"
  },

  "marketData": {
    "currency":          "USD",
    "price":             293.32,
    "priceDate":         "2026-05-09T20:00:00Z",
    "sharesOutstanding": 14687356000,
    "marketCap":         4308095467520,
    "beta_yfinance":     1.065,
    "dividendYield":     0.37,
    "source":            "yfinance via OpenBB 2026-05-10"
  },

  "incomeStatement": {
    "currency": "USD",
    "unit":     1,
    "periods": [
      {
        "fiscalYear":      2024,
        "fiscalPeriod":    "FY",
        "endDate":         "2024-09-28",
        "revenue":         391035000000,
        "grossProfit":     180683000000,
        "operatingIncome": 123216000000,
        "ebitda":          134661000000,
        "netIncome":       93736000000,
        "source":          "yfinance via OpenBB 2026-05-10"
      }
    ]
  },

  "balanceSheet": {
    "currency": "USD",
    "periods": [{
      "fiscalYear":         2024,
      "endDate":            "2024-09-28",
      "totalAssets":        364980000000,
      "totalLiabilities":   308030000000,
      "totalEquity":        56950000000,
      "cashAndEquivalents": 29943000000,
      "totalDebt":          106629000000,
      "source":             "yfinance via OpenBB 2026-05-10"
    }]
  },

  "cashFlow": {
    "currency": "USD",
    "periods": [{
      "fiscalYear":        2024,
      "endDate":           "2024-09-28",
      "operatingCashFlow": 118254000000,
      "capex":             -9447000000,
      "fcf":               108807000000,
      "source":            "yfinance via OpenBB 2026-05-10"
    }]
  },

  "wacc_inputs": {
    "riskFreeRate":      { "value": 0.0441, "source": "OpenBB Federal Reserve 10Y 2026-05-07" },
    "equityRiskPremium": { "value": 0.0500, "source": "tools/defaults.py US default" },
    "countryRiskPremium":{ "value": 0.0000, "source": "tools/defaults.py US default" },
    "industryBeta":      null,
    "marginalTaxRate":   0.21
  },

  "tradingMultiples": {
    "ev":               4370818467520,
    "evToRevenue_LTM":  10.50,
    "evToEbitda_LTM":   30.20,
    "peRatio":          null,
    "asOfPriceDate":    "2026-05-09T20:00:00Z",
    "source":           "derived in normalize.py from OpenBB equity outputs"
  },

  "peers": {
    "suggested_yfinance": [],
    "selected":           ["MSFT", "DELL", "HPQ"]
  },

  "fx": {
    "reportingCurrency": "USD",
    "asOfDate":          null,
    "ratesToUSD":        { "value": null, "source": "OpenBB→yfinance FX (populated by shared.py)" },
    "ratesToEUR":        { "value": null, "source": "OpenBB→yfinance FX (populated by shared.py)" }
  }
}
```

## Field-level rules

- **Region** — derived from Yahoo suffix via `tools/tickers.py:REGION_BY_SUFFIX`.
- **Currency** — yfinance's reporting currency for the company. Comparisons
  across currencies require explicit FX conversion using `_shared/fx/`.
- **Source strings** — must be non-empty for every numeric leaf with an
  external source. Skills use these strings *verbatim* as Excel cell
  comments per the formula/source rules in each upstream skill.
- **`null` values** — explicit signal that the data is unavailable from the
  open-source pipeline; skills must surface this to the user rather than
  fabricating a value.
- **`fiscalYear` derivation** — yfinance via OpenBB returns `fiscal_year=None`.
  `normalize.py` derives the year from the YYYY prefix of `period_ending`.
- **`peers.suggested_yfinance`** — empty in this fork because OpenBB's
  `equity.compare.peers` requires an FMP API key. Users specify peers
  manually via `python tools/fetch.py AAPL --peers MSFT,GOOG,DELL`; the
  list ends up in `peers.selected` and the same data is fetched into
  `./data/<peer>/summary.json` for each peer.
