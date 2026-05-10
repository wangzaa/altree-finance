"""Smoke tests for tools.defaults — static regional default tables."""
import pytest
from tools.defaults import (
    DEFAULT_ERP,
    DEFAULT_MARGINAL_TAX_RATE,
    DEFAULT_COUNTRY_RISK_PREMIUM,
    get_defaults,
)


class TestTablesSpanAllRegions:
    REGIONS = ("US", "UK", "EUROZONE", "JAPAN", "ASIA_DM", "ASIA_EM", "OTHER")

    def test_erp_covers_all_regions(self):
        for r in self.REGIONS:
            assert r in DEFAULT_ERP

    def test_tax_covers_all_regions(self):
        for r in self.REGIONS:
            assert r in DEFAULT_MARGINAL_TAX_RATE

    def test_crp_covers_all_regions(self):
        for r in self.REGIONS:
            assert r in DEFAULT_COUNTRY_RISK_PREMIUM


class TestGetDefaults:
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
