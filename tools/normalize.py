"""Build a canonical summary.json dict from OpenBB outputs.

Pure transformation. No I/O except the small CSV read for risk-free rate
(deliberately co-located here so the function is self-contained for testing).

Inputs are OpenBB result dicts (snake_case keys) from these calls:
  - obb.equity.profile(symbol, provider="yfinance")
  - obb.equity.price.quote(symbol, provider="yfinance")
  - obb.equity.fundamental.income(symbol, provider="yfinance", ...)
  - obb.equity.fundamental.balance(symbol, provider="yfinance", ...)
  - obb.equity.fundamental.cash(symbol, provider="yfinance", ...)

The contract: every numeric leaf field with an external source carries a
sibling ``source`` string, used VERBATIM by skills as cell-comment text.
"""
import csv
from pathlib import Path

from tools.tickers import parse_ticker
from tools.defaults import get_defaults


# Region → human-readable risk-free-rate source label
RISK_FREE_SOURCE_LABEL = {
    "US":       "OpenBB Federal Reserve 10Y",
    "UK":       "OpenBB econdb UK 10Y",
    "EUROZONE": "OpenBB econdb ECB spot 10Y",
    "JAPAN":    "OpenBB econdb Japan 10Y",
    "ASIA_DM":  "OpenBB econdb regional 10Y",
    "ASIA_EM":  "OpenBB econdb regional 10Y",
    "OTHER":    "OpenBB econdb regional 10Y",
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


def _fiscal_year_from_period(period_ending: str | None, explicit: int | None) -> int | None:
    """yfinance via OpenBB returns fiscal_year=None. Derive from period_ending."""
    if explicit is not None:
        return int(explicit)
    if period_ending and isinstance(period_ending, str) and len(period_ending) >= 4:
        try:
            return int(period_ending[:4])
        except ValueError:
            return None
    return None


def _income_statement(income_rows: list[dict], currency: str, source_label: str) -> dict:
    periods = []
    for row in income_rows:
        period_ending = row.get("period_ending")
        if hasattr(period_ending, "isoformat"):
            period_ending = period_ending.isoformat()
        periods.append({
            "fiscalYear":      _fiscal_year_from_period(period_ending, row.get("fiscal_year")),
            "fiscalPeriod":    row.get("fiscal_period") or "FY",
            "endDate":         period_ending,
            "revenue":         row.get("total_revenue"),
            "grossProfit":     row.get("gross_profit"),
            "operatingIncome": row.get("operating_income"),
            "ebitda":          row.get("ebitda"),
            "netIncome":       row.get("net_income"),
            "source":          source_label,
        })
    return {"currency": currency, "unit": 1, "periods": periods}


def _balance_sheet(balance_rows: list[dict], currency: str, source_label: str) -> dict:
    periods = []
    for row in balance_rows:
        period_ending = row.get("period_ending")
        if hasattr(period_ending, "isoformat"):
            period_ending = period_ending.isoformat()
        periods.append({
            "fiscalYear":         _fiscal_year_from_period(period_ending, row.get("fiscal_year")),
            "endDate":            period_ending,
            "totalAssets":        row.get("total_assets"),
            "totalLiabilities":   row.get("total_liabilities_net_minority_interest"),
            "totalEquity":        row.get("total_common_equity"),
            "cashAndEquivalents": row.get("cash_and_cash_equivalents"),
            "totalDebt":          row.get("total_debt"),
            "source":             source_label,
        })
    return {"currency": currency, "periods": periods}


def _cash_flow(cash_rows: list[dict], currency: str, source_label: str) -> dict:
    periods = []
    for row in cash_rows:
        period_ending = row.get("period_ending")
        if hasattr(period_ending, "isoformat"):
            period_ending = period_ending.isoformat()
        periods.append({
            "fiscalYear":         _fiscal_year_from_period(period_ending, row.get("fiscal_year")),
            "endDate":            period_ending,
            "operatingCashFlow":  row.get("operating_cash_flow"),
            "capex":              row.get("capital_expenditure"),
            "fcf":                row.get("free_cash_flow"),
            "source":             source_label,
        })
    return {"currency": currency, "periods": periods}


def _trading_multiples(profile: dict, quote: dict, balance_rows: list[dict], income_rows: list[dict]) -> dict:
    market_cap = profile.get("market_cap")
    bs_latest = balance_rows[0] if balance_rows else {}
    total_debt = bs_latest.get("total_debt") or 0
    cash = bs_latest.get("cash_and_cash_equivalents") or 0
    ev = market_cap + total_debt - cash if market_cap is not None else None

    is_latest = income_rows[0] if income_rows else {}
    revenue = is_latest.get("total_revenue")
    ebitda = is_latest.get("ebitda")

    price_date = quote.get("last_timestamp") if quote else None
    if hasattr(price_date, "isoformat"):
        price_date = price_date.isoformat()

    return {
        "ev":                 ev,
        "evToRevenue_LTM":    (ev / revenue) if (ev is not None and revenue) else None,
        "evToEbitda_LTM":     (ev / ebitda)  if (ev is not None and ebitda)  else None,
        "peRatio":            (quote or {}).get("pe_ratio"),
        "asOfPriceDate":      price_date,
        "source":             "derived in normalize.py from OpenBB equity outputs",
    }


def build_summary(
    ticker: str,
    profile: dict,
    quote: dict,
    income: list[dict],
    balance: list[dict],
    cash: list[dict],
    rate_csv_path: Path,
    fetched_at: str,
    peers: list[str] | None = None,
    as_of: str | None = None,
) -> dict:
    """Build the canonical summary.json structure from OpenBB outputs."""
    parsed = parse_ticker(ticker)
    region = parsed["region"]
    defaults = get_defaults(region)

    rate_value, rate_date = latest_rate_from_csv(rate_csv_path)
    rf_source = f"{RISK_FREE_SOURCE_LABEL[region]} {rate_date}"
    yf_source = f"yfinance via OpenBB {fetched_at[:10]}"

    currency = profile.get("currency") or "USD"
    # yfinance via OpenBB returns industry=None; the human-readable value
    # is in industry_category. Fall back across the chain.
    industry = (
        profile.get("industry")
        or profile.get("industry_group")
        or profile.get("industry_category")
    )

    quote = quote or {}
    price = quote.get("last_price")
    price_date = quote.get("last_timestamp")
    if hasattr(price_date, "isoformat"):
        price_date = price_date.isoformat()

    return {
        "ticker":         ticker,
        "directoryName":  parsed["dir_name"],
        "region":         region,
        "asOf":           as_of or fetched_at[:10],
        "fetchedAt":      fetched_at,
        "company": {
            "name":              profile.get("name"),
            "sector":            profile.get("sector"),
            "industry":          industry,
            "description_short": profile.get("long_description") or profile.get("short_description"),
            "narrative_path":    "raw/wikipedia_summary.json",
        },
        "marketData": {
            "currency":          currency,
            "price":             price,
            "priceDate":         price_date,
            "sharesOutstanding": profile.get("shares_outstanding"),
            "marketCap":         profile.get("market_cap"),
            "beta_yfinance":     profile.get("beta"),
            "dividendYield":     profile.get("dividend_yield"),
            "source":            yf_source,
        },
        "incomeStatement": _income_statement(income, currency, yf_source),
        "balanceSheet":    _balance_sheet(balance, currency, yf_source),
        "cashFlow":        _cash_flow(cash, currency, yf_source),
        "wacc_inputs": {
            "riskFreeRate": {
                "value":  rate_value,
                "source": rf_source,
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
        "tradingMultiples": _trading_multiples(profile, quote, balance, income),
        "peers": {
            "suggested_yfinance": peers or [],
            "selected":           [],
        },
        "fx": {
            "reportingCurrency": currency,
            "asOfDate":          None,
            "ratesToUSD":        {"value": None, "source": "OpenBB→yfinance FX (populated by shared.py)"},
            "ratesToEUR":        {"value": None, "source": "OpenBB→yfinance FX (populated by shared.py)"},
        },
    }
