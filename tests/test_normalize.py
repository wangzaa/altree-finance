"""Tests for tools.normalize — pure transformation, fixture-driven (OpenBB schema)."""
import pytest
from tools.normalize import build_summary, latest_rate_from_csv


def _build(profile, quote, income, balance, cash, rate_path, ticker="AAPL", peers=None):
    return build_summary(
        ticker=ticker,
        profile=profile,
        quote=quote,
        income=income,
        balance=balance,
        cash=cash,
        rate_csv_path=rate_path,
        fetched_at="2026-05-10T14:32:00Z",
        peers=peers or [],
    )


class TestLatestRateFromCsv:
    def test_returns_most_recent_row(self, us_10y_csv_path):
        rate, date = latest_rate_from_csv(us_10y_csv_path)
        assert rate == 0.0428
        assert date == "2026-05-09"


class TestBuildSummaryStructure:
    def test_top_level_keys_present(
        self, openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
        openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path
    ):
        s = _build(openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
                   openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path)
        for key in (
            "ticker", "directoryName", "region", "asOf", "fetchedAt",
            "company", "marketData", "incomeStatement", "balanceSheet",
            "cashFlow", "wacc_inputs", "tradingMultiples", "peers", "fx",
        ):
            assert key in s, f"summary.json missing key: {key}"

    def test_ticker_and_directory(
        self, openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
        openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path
    ):
        s = _build(openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
                   openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path)
        assert s["ticker"] == "AAPL"
        assert s["directoryName"] == "AAPL"
        assert s["region"] == "US"


class TestCompanyBlock:
    def test_company_fields(
        self, openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
        openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path
    ):
        s = _build(openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
                   openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path)
        assert s["company"]["name"] == "Apple Inc."
        assert s["company"]["sector"] == "Technology"
        # OpenBB's `industry` is None for yfinance; we fall back to industry_category
        assert s["company"]["industry"] == "Consumer Electronics"
        assert "designs" in s["company"]["description_short"]


class TestMarketData:
    def test_market_data_with_source(
        self, openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
        openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path
    ):
        s = _build(openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
                   openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path)
        md = s["marketData"]
        assert md["currency"] == "USD"
        assert md["price"] == 187.45
        assert md["marketCap"] == 2900000000000
        assert md["sharesOutstanding"] == 15500000000
        assert md["beta_yfinance"] == 1.27
        assert "yfinance" in md["source"].lower()


class TestIncomeStatement:
    def test_periods_present_with_source(
        self, openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
        openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path
    ):
        s = _build(openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
                   openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path)
        is_block = s["incomeStatement"]
        assert is_block["currency"] == "USD"
        assert len(is_block["periods"]) == 2
        latest = is_block["periods"][0]
        # OpenBB returns fiscal_year=None; we derive from period_ending
        assert latest["fiscalYear"] == 2024
        assert latest["revenue"] == 391035000000
        assert latest["ebitda"] == 134661000000
        assert "yfinance" in latest["source"].lower()


class TestBalanceSheet:
    def test_balance_fields_mapped(
        self, openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
        openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path
    ):
        s = _build(openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
                   openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path)
        bs = s["balanceSheet"]["periods"][0]
        assert bs["totalAssets"] == 364980000000
        assert bs["totalLiabilities"] == 308030000000
        assert bs["totalEquity"] == 56950000000
        assert bs["cashAndEquivalents"] == 29943000000
        assert bs["totalDebt"] == 106629000000


class TestCashFlow:
    def test_cash_fields_mapped(
        self, openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
        openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path
    ):
        s = _build(openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
                   openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path)
        cf = s["cashFlow"]["periods"][0]
        assert cf["operatingCashFlow"] == 118254000000
        assert cf["capex"] == -9447000000
        assert cf["fcf"] == 108807000000


class TestWACCInputs:
    def test_us_wacc_inputs_use_us_treasury_and_us_defaults(
        self, openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
        openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path
    ):
        s = _build(openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
                   openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path)
        w = s["wacc_inputs"]
        assert w["riskFreeRate"]["value"] == 0.0428
        assert "Reserve" in w["riskFreeRate"]["source"] or "10Y" in w["riskFreeRate"]["source"]
        assert w["equityRiskPremium"]["value"] == 0.05
        assert "defaults" in w["equityRiskPremium"]["source"].lower()
        assert w["marginalTaxRate"] == 0.21
        assert w["countryRiskPremium"]["value"] == 0.0


class TestTradingMultiples:
    def test_ev_to_ebitda_computed_from_market_and_fundamentals(
        self, openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
        openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path
    ):
        s = _build(openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
                   openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path)
        tm = s["tradingMultiples"]
        expected_ev = 2_900_000_000_000 + 106_629_000_000 - 29_943_000_000
        assert tm["ev"] == expected_ev
        expected_ev_ebitda = expected_ev / 134_661_000_000
        assert tm["evToEbitda_LTM"] == pytest.approx(expected_ev_ebitda, rel=1e-4)
        assert tm["peRatio"] == 30.94
        assert "derived" in tm["source"].lower() or "openbb" in tm["source"].lower()


class TestSourceCitations:
    def test_all_sourced_fields_have_non_empty_source(
        self, openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
        openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path
    ):
        s = _build(openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
                   openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path)
        for path, value in [
            ("marketData.source", s["marketData"]["source"]),
            ("incomeStatement.periods[0].source", s["incomeStatement"]["periods"][0]["source"]),
            ("wacc_inputs.riskFreeRate.source", s["wacc_inputs"]["riskFreeRate"]["source"]),
            ("wacc_inputs.equityRiskPremium.source", s["wacc_inputs"]["equityRiskPremium"]["source"]),
            ("wacc_inputs.countryRiskPremium.source", s["wacc_inputs"]["countryRiskPremium"]["source"]),
            ("tradingMultiples.source", s["tradingMultiples"]["source"]),
        ]:
            assert isinstance(value, str) and len(value) > 0, f"{path} has empty source"


class TestNonUSTicker:
    def test_japanese_ticker_uses_japan_region_and_defaults(
        self, openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
        openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path
    ):
        profile = dict(openbb_profile_aapl)
        profile["symbol"] = "7203.T"
        profile["currency"] = "JPY"
        s = _build(profile, openbb_quote_aapl, openbb_income_aapl,
                   openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path,
                   ticker="7203.T")
        assert s["region"] == "JAPAN"
        assert s["directoryName"] == "7203_T"
        assert s["wacc_inputs"]["equityRiskPremium"]["value"] == 0.05
        assert s["wacc_inputs"]["marginalTaxRate"] == 0.30


class TestFiscalYearDerivation:
    def test_derives_year_from_period_ending_when_explicit_is_none(
        self, openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
        openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path
    ):
        # OpenBB→yfinance returns fiscal_year=None; verify we derive 2024 from
        # period_ending="2024-09-28"
        s = _build(openbb_profile_aapl, openbb_quote_aapl, openbb_income_aapl,
                   openbb_balance_aapl, openbb_cash_aapl, us_10y_csv_path)
        assert s["incomeStatement"]["periods"][0]["fiscalYear"] == 2024
        assert s["incomeStatement"]["periods"][1]["fiscalYear"] == 2023
        assert s["balanceSheet"]["periods"][0]["fiscalYear"] == 2024
        assert s["cashFlow"]["periods"][0]["fiscalYear"] == 2024
