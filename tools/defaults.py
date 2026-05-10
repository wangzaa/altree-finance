"""Regional default values for WACC inputs that have no open-source feed.

These tables are stale by construction — review annually (typically against
Damodaran's published series each January) and bump versions accordingly.

All overridable per-run via fetch.py CLI flags.
"""

DEFAULT_ERP = {
    "US":         0.0500,
    "UK":         0.0550,
    "EUROZONE":   0.0550,
    "JAPAN":      0.0500,
    "ASIA_DM":    0.0550,    # HK, SG, AU, NZ
    "ASIA_EM":    0.0750,    # IN, CN A-shares (when accessible)
    "OTHER":      0.0700,
}

DEFAULT_MARGINAL_TAX_RATE = {
    "US":         0.21,
    "UK":         0.25,
    "EUROZONE":   0.25,      # rough average; varies by country
    "JAPAN":      0.30,
    "ASIA_DM":    0.20,
    "ASIA_EM":    0.25,
    "OTHER":      0.25,
}

DEFAULT_COUNTRY_RISK_PREMIUM = {
    "US":         0.0000,
    "UK":         0.0000,
    "EUROZONE":   0.0000,
    "JAPAN":      0.0000,
    "ASIA_DM":    0.0000,
    "ASIA_EM":    0.0250,
    "OTHER":      0.0300,
}


def get_defaults(region: str) -> dict:
    """Return all WACC-input defaults for a region.

    Falls back to ``OTHER`` for unknown regions.
    """
    fallback = "OTHER"
    return {
        "equityRiskPremium":  DEFAULT_ERP.get(region,                  DEFAULT_ERP[fallback]),
        "marginalTaxRate":    DEFAULT_MARGINAL_TAX_RATE.get(region,    DEFAULT_MARGINAL_TAX_RATE[fallback]),
        "countryRiskPremium": DEFAULT_COUNTRY_RISK_PREMIUM.get(region, DEFAULT_COUNTRY_RISK_PREMIUM[fallback]),
    }
