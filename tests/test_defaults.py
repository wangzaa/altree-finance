"""Smoke tests for tools.defaults — regional + country-specific tables."""
import pytest
from tools.defaults import (
    DEFAULT_ERP,
    DEFAULT_MARGINAL_TAX_RATE,
    MARGINAL_TAX_BY_SUFFIX,
    DEFAULT_COUNTRY_RISK_PREMIUM,
    get_defaults,
)


class TestTablesSpanAllRegions:
    REGIONS = ("US", "UK", "EUROZONE", "JAPAN", "ASIA_DM", "ASIA_EM", "OTHER")

    def test_erp_covers_all_regions(self):
        for r in self.REGIONS:
            assert r in DEFAULT_ERP

    def test_tax_regional_fallback_covers_all_regions(self):
        for r in self.REGIONS:
            assert r in DEFAULT_MARGINAL_TAX_RATE

    def test_crp_covers_all_regions(self):
        for r in self.REGIONS:
            assert r in DEFAULT_COUNTRY_RISK_PREMIUM


class TestCountryTaxTableCoversTickerSuffixes:
    """The per-suffix tax table should cover at least the major suffixes
    that REGION_BY_SUFFIX in tools/tickers.py also covers."""

    def test_major_suffixes_present(self):
        for suffix in ("", ".L", ".PA", ".DE", ".T", ".HK", ".KS", ".SZ"):
            assert suffix in MARGINAL_TAX_BY_SUFFIX, f"missing {suffix!r}"


class TestGetDefaultsRegionalOnly:
    """When called without a suffix, get_defaults uses regional fallbacks."""

    def test_us_defaults(self):
        d = get_defaults("US")
        assert d["equityRiskPremium"] == 0.05
        assert d["marginalTaxRate"] == 0.21
        assert d["countryRiskPremium"] == 0.0

    def test_emerging_market_has_country_premium(self):
        d = get_defaults("ASIA_EM")
        assert d["countryRiskPremium"] > 0.0

    def test_unknown_region_falls_back_to_other(self):
        d = get_defaults("MARS")
        assert d == get_defaults("OTHER")


class TestGetDefaultsCountrySpecific:
    """When a suffix is supplied, marginal tax rate uses the country-specific
    value rather than the regional bucket."""

    def test_germany_uses_country_tax(self):
        d = get_defaults("EUROZONE", suffix=".DE")
        assert d["marginalTaxRate"] == 0.30   # not 0.25 EUROZONE bucket
        assert d["equityRiskPremium"] == 0.0550   # ERP still regional

    def test_ireland_uses_country_tax(self):
        d = get_defaults("EUROZONE", suffix=".IR")
        assert d["marginalTaxRate"] == 0.125

    def test_hong_kong_uses_country_tax(self):
        d = get_defaults("ASIA_DM", suffix=".HK")
        assert d["marginalTaxRate"] == 0.165   # not 0.20 ASIA_DM bucket

    def test_brazil_uses_country_tax(self):
        d = get_defaults("OTHER", suffix=".SA")
        assert d["marginalTaxRate"] == 0.34

    def test_us_no_suffix_uses_country_tax(self):
        # Empty suffix corresponds to US tickers
        d = get_defaults("US", suffix="")
        assert d["marginalTaxRate"] == 0.21

    def test_unknown_suffix_falls_back_to_region(self):
        # Suffix not in the per-country table → fall through to region default
        d = get_defaults("EUROZONE", suffix=".XX")
        assert d["marginalTaxRate"] == 0.25


class TestSanityRanges:
    def test_erp_in_plausible_range(self):
        for region, value in DEFAULT_ERP.items():
            assert 0.03 <= value <= 0.10, f"{region} ERP {value} outside plausible range"

    def test_country_tax_in_plausible_range(self):
        for suffix, value in MARGINAL_TAX_BY_SUFFIX.items():
            assert 0.10 <= value <= 0.40, f"{suffix!r} tax {value} outside plausible range"

    def test_regional_tax_in_plausible_range(self):
        for region, value in DEFAULT_MARGINAL_TAX_RATE.items():
            assert 0.15 <= value <= 0.40, f"{region} tax {value} outside plausible range"

    def test_crp_in_plausible_range(self):
        for region, value in DEFAULT_COUNTRY_RISK_PREMIUM.items():
            assert 0.0 <= value <= 0.10, f"{region} CRP {value} outside plausible range"


class TestSanityRanges:
    def test_erp_in_plausible_range(self):
        for region, value in DEFAULT_ERP.items():
            assert 0.03 <= value <= 0.10, f"{region} ERP {value} outside plausible range"

    def test_tax_in_plausible_range(self):
        for region, value in DEFAULT_MARGINAL_TAX_RATE.items():
            assert 0.15 <= value <= 0.40, f"{region} tax {value} outside plausible range"

    def test_crp_in_plausible_range(self):
        for region, value in DEFAULT_COUNTRY_RISK_PREMIUM.items():
            assert 0.0 <= value <= 0.10, f"{region} CRP {value} outside plausible range"
