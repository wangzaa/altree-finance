"""Tests for tools.normalize — pure transformation, fixture-driven."""
import pytest
from tools.normalize import build_summary, latest_rate_from_csv


class TestLatestRateFromCsv:
    def test_returns_most_recent_row(self, us_10y_csv_path):
        rate, date = latest_rate_from_csv(us_10y_csv_path)
        assert rate == 0.0428
        assert date == "2026-05-09"


class TestBuildSummaryStructure:
    def test_top_level_keys_present(
        self, yfinance_info_aapl, yfinance_financials_aapl, us_10y_csv_path
    ):
        summary = build_summary(
            ticker="AAPL",
            yfinance_info=yfinance_info_aapl,
            yfinance_financials=yfinance_financials_aapl,
            rate_csv_path=us_10y_csv_path,
            fetched_at="2026-05-10T14:32:00Z",
        )
        for key in (
            "ticker", "directoryName", "region", "asOf", "fetchedAt",
            "company", "marketData", "incomeStatement", "balanceSheet",
            "cashFlow", "wacc_inputs", "tradingMultiples", "peers", "fx",
        ):
            assert key in summary, f"summary.json missing key: {key}"

    def test_ticker_and_directory(
        self, yfinance_info_aapl, yfinance_financials_aapl, us_10y_csv_path
    ):
        summary = build_summary(
            "AAPL", yfinance_info_aapl, yfinance_financials_aapl, us_10y_csv_path,
            fetched_at="2026-05-10T14:32:00Z",
        )
        assert summary["ticker"] == "AAPL"
        assert summary["directoryName"] == "AAPL"
        assert summary["region"] == "US"


class TestCompanyBlock:
    def test_company_fields(
        self, yfinance_info_aapl, yfinance_financials_aapl, us_10y_csv_path
    ):
        s = build_summary(
            "AAPL", yfinance_info_aapl, yfinance_financials_aapl, us_10y_csv_path,
            fetched_at="2026-05-10T14:32:00Z",
        )
        assert s["company"]["name"] == "Apple Inc."
        assert s["company"]["sector"] == "Technology"
        assert s["company"]["industry"] == "Consumer Electronics"
        assert "designs" in s["company"]["description_short"]


class TestMarketData:
    def test_market_data_with_source(
        self, yfinance_info_aapl, yfinance_financials_aapl, us_10y_csv_path
    ):
        s = build_summary(
            "AAPL", yfinance_info_aapl, yfinance_financials_aapl, us_10y_csv_path,
            fetched_at="2026-05-10T14:32:00Z",
        )
        md = s["marketData"]
        assert md["currency"] == "USD"
        assert md["price"] == 187.45
        assert md["marketCap"] == 2900000000000
        assert md["sharesOutstanding"] == 15500000000
        assert md["beta_yfinance"] == 1.27
        assert "yfinance" in md["source"].lower()


class TestIncomeStatement:
    def test_periods_present_with_source(
        self, yfinance_info_aapl, yfinance_financials_aapl, us_10y_csv_path
    ):
        s = build_summary(
            "AAPL", yfinance_info_aapl, yfinance_financials_aapl, us_10y_csv_path,
            fetched_at="2026-05-10T14:32:00Z",
        )
        is_block = s["incomeStatement"]
        assert is_block["currency"] == "USD"
        assert len(is_block["periods"]) == 2
        latest = is_block["periods"][0]
        assert latest["fiscalYear"] == 2024
        assert latest["revenue"] == 391035000000
        assert latest["ebitda"] == 134661000000
        assert "yfinance" in latest["source"].lower()


class TestWACCInputs:
    def test_us_wacc_inputs_use_us_treasury_and_us_defaults(
        self, yfinance_info_aapl, yfinance_financials_aapl, us_10y_csv_path
    ):
        s = build_summary(
            "AAPL", yfinance_info_aapl, yfinance_financials_aapl, us_10y_csv_path,
            fetched_at="2026-05-10T14:32:00Z",
        )
        w = s["wacc_inputs"]
        assert w["riskFreeRate"]["value"] == 0.0428
        assert "Treasury" in w["riskFreeRate"]["source"] or "10Y" in w["riskFreeRate"]["source"]
        assert w["equityRiskPremium"]["value"] == 0.05
        assert "defaults" in w["equityRiskPremium"]["source"].lower()
        assert w["marginalTaxRate"] == 0.21
        assert w["countryRiskPremium"]["value"] == 0.0


class TestTradingMultiples:
    def test_ev_to_ebitda_computed_from_market_and_fundamentals(
        self, yfinance_info_aapl, yfinance_financials_aapl, us_10y_csv_path
    ):
        s = build_summary(
            "AAPL", yfinance_info_aapl, yfinance_financials_aapl, us_10y_csv_path,
            fetched_at="2026-05-10T14:32:00Z",
        )
        tm = s["tradingMultiples"]
        expected_ev = 2_900_000_000_000 + 106_629_000_000 - 29_943_000_000
        assert tm["ev"] == expected_ev
        expected_ev_ebitda = expected_ev / 134_661_000_000
        assert tm["evToEbitda_LTM"] == pytest.approx(expected_ev_ebitda, rel=1e-4)
        assert tm["peRatio"] == 30.94
        assert "derived" in tm["source"].lower() or "normalize" in tm["source"].lower()


class TestSourceCitations:
    """Every numeric leaf with an explicit source must have a non-empty source string."""

    def test_all_sourced_fields_have_non_empty_source(
        self, yfinance_info_aapl, yfinance_financials_aapl, us_10y_csv_path
    ):
        s = build_summary(
            "AAPL", yfinance_info_aapl, yfinance_financials_aapl, us_10y_csv_path,
            fetched_at="2026-05-10T14:32:00Z",
        )
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
        self, yfinance_info_aapl, yfinance_financials_aapl, us_10y_csv_path
    ):
        info = dict(yfinance_info_aapl)
        info["symbol"] = "7203.T"
        info["currency"] = "JPY"
        s = build_summary(
            "7203.T", info, yfinance_financials_aapl, us_10y_csv_path,
            fetched_at="2026-05-10T14:32:00Z",
        )
        assert s["region"] == "JAPAN"
        assert s["directoryName"] == "7203_T"
        assert s["wacc_inputs"]["equityRiskPremium"]["value"] == 0.05
        assert s["wacc_inputs"]["marginalTaxRate"] == 0.30
