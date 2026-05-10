"""Build a canonical summary.json dict from raw OpenBB / yfinance outputs.

Pure transformation. No I/O except the small CSV read for risk-free rate
(deliberately co-located here so the function is self-contained for testing).

The key contract: every numeric leaf field that has an external source carries
a sibling ``source`` string, used VERBATIM by skills as cell-comment text.
"""
import csv
from pathlib import Path
from typing import Any

from tools.tickers import parse_ticker
from tools.defaults import get_defaults


# Map region → human-readable risk-free-rate source label
RISK_FREE_SOURCE_LABEL = {
    "US":       "OpenBB US Treasury 10Y",
    "UK":       "OpenBB BoE 10Y",
    "EUROZONE": "OpenBB ECB 10Y benchmark",
    "JAPAN":    "OpenBB BoJ 10Y JGB",
    "ASIA_DM":  "OpenBB OECD/BIS regional 10Y",
    "ASIA_EM":  "OpenBB OECD/BIS regional 10Y",
    "OTHER":    "OpenBB OECD/BIS regional 10Y",
}


def latest_rate_from_csv(csv_path: Path) -> tuple[float, str]:
    """Read a date,rate CSV and return the (rate, date) of the latest row."""
    rows = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append((row["date"], float(row["rate"])))
    rows.sort(key=lambda r: r[0])
    date, rate = rows[-1]
    return rate, date


def _income_statement(financials: dict, source_label: str) -> dict:
    periods = []
    for row in financials.get("income_statement", []):
        periods.append({
            "fiscalYear":      row["fiscal_year"],
            "fiscalPeriod":    row.get("fiscal_period", "FY"),
            "endDate":         row["period_ending"],
            "revenue":         row["total_revenue"],
            "grossProfit":     row.get("gross_profit"),
            "operatingIncome": row.get("operating_income"),
            "ebitda":          row.get("ebitda"),
            "netIncome":       row.get("net_income"),
            "source":          source_label,
        })
    currency = "USD"  # default; overridden by caller if known
    return {"currency": currency, "unit": 1, "periods": periods}


def _balance_sheet(financials: dict, source_label: str) -> dict:
    periods = []
    for row in financials.get("balance_sheet", []):
        periods.append({
            "fiscalYear":         row["fiscal_year"],
            "endDate":            row["period_ending"],
            "totalAssets":        row.get("total_assets"),
            "totalLiabilities":   row.get("total_liabilities"),
            "totalEquity":        row.get("total_equity"),
            "cashAndEquivalents": row.get("cash_and_equivalents"),
            "totalDebt":          row.get("total_debt"),
            "source":             source_label,
        })
    return {"currency": "USD", "periods": periods}


def _cash_flow(financials: dict, source_label: str) -> dict:
    periods = []
    for row in financials.get("cash_flow", []):
        periods.append({
            "fiscalYear":         row["fiscal_year"],
            "endDate":            row["period_ending"],
            "operatingCashFlow":  row.get("operating_cash_flow"),
            "capex":              row.get("capital_expenditures"),
            "fcf":                row.get("free_cash_flow"),
            "source":             source_label,
        })
    return {"currency": "USD", "periods": periods}


def _trading_multiples(info: dict, financials: dict) -> dict:
    market_cap = info.get("marketCap")
    bs_latest = (financials.get("balance_sheet") or [{}])[0]
    total_debt = bs_latest.get("total_debt", 0) or 0
    cash = bs_latest.get("cash_and_equivalents", 0) or 0
    ev = market_cap + total_debt - cash if market_cap is not None else None

    is_latest = (financials.get("income_statement") or [{}])[0]
    revenue = is_latest.get("total_revenue")
    ebitda = is_latest.get("ebitda")

    return {
        "ev":                 ev,
        "evToRevenue_LTM":    (ev / revenue) if (ev is not None and revenue) else None,
        "evToEbitda_LTM":     (ev / ebitda)  if (ev is not None and ebitda)  else None,
        "peRatio":            info.get("trailingPE"),
        "asOfPriceDate":      None,
        "source":             "derived in normalize.py from yfinance financials + market data",
    }


def build_summary(
    ticker: str,
    yfinance_info: dict,
    yfinance_financials: dict,
    rate_csv_path: Path,
    fetched_at: str,
    as_of: str | None = None,
) -> dict:
    """Build the canonical summary.json structure."""
    parsed = parse_ticker(ticker)
    region = parsed["region"]
    defaults = get_defaults(region)

    rate_value, rate_date = latest_rate_from_csv(rate_csv_path)
    rf_source_label = f"{RISK_FREE_SOURCE_LABEL[region]} {rate_date}"
    yf_source = f"yfinance via OpenBB {fetched_at[:10]}"

    return {
        "ticker":         ticker,
        "directoryName":  parsed["dir_name"],
        "region":         region,
        "asOf":           as_of or fetched_at[:10],
        "fetchedAt":      fetched_at,
        "company": {
            "name":              yfinance_info.get("longName"),
            "sector":            yfinance_info.get("sector"),
            "industry":          yfinance_info.get("industry"),
            "description_short": yfinance_info.get("longBusinessSummary"),
            "narrative_path":    "raw/wikipedia_summary.json",
        },
        "marketData": {
            "currency":          yfinance_info.get("currency"),
            "price":             yfinance_info.get("regularMarketPrice"),
            "priceDate":         None,
            "sharesOutstanding": yfinance_info.get("sharesOutstanding"),
            "marketCap":         yfinance_info.get("marketCap"),
            "beta_yfinance":     yfinance_info.get("beta"),
            "dividendYield":     yfinance_info.get("dividendYield"),
            "source":            yf_source,
        },
        "incomeStatement": _income_statement(yfinance_financials, yf_source),
        "balanceSheet":    _balance_sheet(yfinance_financials, yf_source),
        "cashFlow":        _cash_flow(yfinance_financials, yf_source),
        "wacc_inputs": {
            "riskFreeRate": {
                "value":  rate_value,
                "source": rf_source_label,
            },
            "equityRiskPremium": {
                "value":  defaults["equityRiskPremium"],
                "source": f"tools/defaults.py {region} default",
            },
            "countryRiskPremium": {
                "value":  defaults["countryRiskPremium"],
                "source": f"tools/defaults.py {region} default",
            },
            "industryBeta":    None,
            "marginalTaxRate": defaults["marginalTaxRate"],
        },
        "tradingMultiples": _trading_multiples(yfinance_info, yfinance_financials),
        "peers": {
            "suggested_yfinance": [],
            "selected":           [],
        },
        "fx": {
            "reportingCurrency": yfinance_info.get("currency"),
            "asOfDate":          None,
            "ratesToUSD":        {"value": None, "source": "ECB via OpenBB (populated by shared.py)"},
            "ratesToEUR":        {"value": None, "source": "ECB via OpenBB (populated by shared.py)"},
        },
    }
