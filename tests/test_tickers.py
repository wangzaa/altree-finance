"""Tests for tools.tickers — pure logic, no I/O."""
import pytest
from tools.tickers import parse_ticker, to_dir_name, region_for, REGION_BY_SUFFIX


class TestParseTickerRegion:
    def test_us_no_suffix(self):
        result = parse_ticker("AAPL")
        assert result["ticker"] == "AAPL"
        assert result["suffix"] == ""
        assert result["region"] == "US"
        assert result["dir_name"] == "AAPL"

    def test_uk_lse(self):
        result = parse_ticker("BARC.L")
        assert result["region"] == "UK"
        assert result["suffix"] == ".L"
        assert result["dir_name"] == "BARC_L"

    def test_japan_tse(self):
        result = parse_ticker("7203.T")
        assert result["region"] == "JAPAN"
        assert result["dir_name"] == "7203_T"

    def test_eurozone_paris(self):
        assert parse_ticker("MC.PA")["region"] == "EUROZONE"

    def test_eurozone_frankfurt(self):
        assert parse_ticker("SAP.DE")["region"] == "EUROZONE"

    def test_eurozone_amsterdam(self):
        assert parse_ticker("ASML.AS")["region"] == "EUROZONE"

    def test_eurozone_milan(self):
        assert parse_ticker("ENI.MI")["region"] == "EUROZONE"

    def test_eurozone_madrid(self):
        assert parse_ticker("ITX.MC")["region"] == "EUROZONE"

    def test_hong_kong(self):
        result = parse_ticker("0700.HK")
        assert result["region"] == "ASIA_DM"
        assert result["dir_name"] == "0700_HK"

    def test_australia(self):
        assert parse_ticker("BHP.AX")["region"] == "ASIA_DM"

    def test_singapore(self):
        assert parse_ticker("D05.SI")["region"] == "ASIA_DM"

    def test_india_nse(self):
        assert parse_ticker("RELIANCE.NS")["region"] == "ASIA_EM"

    def test_india_bse(self):
        assert parse_ticker("RELIANCE.BO")["region"] == "ASIA_EM"

    def test_china_shenzhen(self):
        assert parse_ticker("300750.SZ")["region"] == "ASIA_EM"

    def test_china_shanghai(self):
        assert parse_ticker("600519.SS")["region"] == "ASIA_EM"

    def test_korea_kospi(self):
        assert parse_ticker("005930.KS")["region"] == "ASIA_DM"

    def test_korea_kosdaq(self):
        assert parse_ticker("035720.KQ")["region"] == "ASIA_DM"

    def test_taiwan(self):
        assert parse_ticker("2330.TW")["region"] == "ASIA_DM"

    def test_new_zealand(self):
        assert parse_ticker("FPH.NZ")["region"] == "ASIA_DM"

    def test_germany_frankfurt(self):
        assert parse_ticker("BMW.F")["region"] == "EUROZONE"

    def test_belgium(self):
        assert parse_ticker("AB.BR")["region"] == "EUROZONE"

    def test_switzerland(self):
        # Switzerland is non-Eurozone but mapped to EUROZONE defaults
        assert parse_ticker("NESN.SW")["region"] == "EUROZONE"

    def test_sweden(self):
        assert parse_ticker("VOLV-B.ST")["region"] == "EUROZONE"

    def test_canada(self):
        # Toronto mapped to OTHER (defaults are closer than US tax)
        assert parse_ticker("RY.TO")["region"] == "OTHER"

    def test_brazil(self):
        assert parse_ticker("VALE3.SA")["region"] == "OTHER"

    def test_unknown_suffix_falls_back_to_other(self):
        assert parse_ticker("FOO.XX")["region"] == "OTHER"


class TestToDirName:
    def test_no_suffix_unchanged(self):
        assert to_dir_name("AAPL") == "AAPL"

    def test_period_replaced_with_underscore(self):
        assert to_dir_name("7203.T") == "7203_T"

    def test_uk_period_replaced(self):
        assert to_dir_name("BARC.L") == "BARC_L"


class TestRegionFor:
    def test_convenience_us(self):
        assert region_for("AAPL") == "US"

    def test_convenience_japan(self):
        assert region_for("7203.T") == "JAPAN"


class TestRegionMappingTable:
    def test_table_includes_all_target_regions(self):
        regions = set(REGION_BY_SUFFIX.values())
        assert "US" in regions
        assert "UK" in regions
        assert "EUROZONE" in regions
        assert "JAPAN" in regions
        assert "ASIA_DM" in regions
        assert "ASIA_EM" in regions
