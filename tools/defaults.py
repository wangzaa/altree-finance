"""Default values for WACC inputs that have no open-source feed.

ERP and country risk premium are keyed by region (broad market grouping).
Marginal tax rate is keyed by Yahoo suffix (country-level) because effective
corporate tax rates vary materially across countries within a region — a
single regional bucket would over- or under-state Germany (30%), Ireland
(12.5%), Switzerland (~18%), Hong Kong (16.5%), Brazil (34%), etc.

All tables are stale by construction — review annually (typically against
OECD published statutory rates and Damodaran's ERP series each January).

All overridable per-run via fetch.py CLI flags (--erp, --tax-rate).
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

# Country-level marginal tax rates keyed by Yahoo Finance suffix.
# Values reflect statutory corporate income tax (with major surtaxes
# included where universally applied — e.g. German trade tax, Italian
# IRES). Stale by construction; review annually against OECD data.
MARGINAL_TAX_BY_SUFFIX = {
    # United States
    "":      0.21,    # federal (state taxes additive but vary; treat 21% as baseline)
    # UK
    ".L":    0.25,    # Corporation Tax
    ".IL":   0.25,
    # Eurozone
    ".PA":   0.25,    # France
    ".DE":   0.30,    # Germany — corporate (15%) + solidarity (0.825%) + trade tax (~14%)
    ".F":    0.30,    # Germany — Frankfurt
    ".AS":   0.258,   # Netherlands
    ".MI":   0.24,    # Italy — IRES (excludes regional IRAP ~3.9%)
    ".MC":   0.25,    # Spain
    ".BR":   0.25,    # Belgium
    ".LS":   0.21,    # Portugal
    ".HE":   0.20,    # Finland
    ".VI":   0.25,    # Austria
    ".IR":   0.125,   # Ireland — trading income only
    ".AT":   0.22,    # Greece
    # Developed Europe non-Eurozone
    ".SW":   0.18,    # Switzerland — effective avg; varies 12-21% by canton
    ".OL":   0.22,    # Norway
    ".ST":   0.206,   # Sweden
    ".CO":   0.22,    # Denmark
    # Japan
    ".T":    0.30,    # national + local effective
    # Asia DM
    ".HK":   0.165,   # Hong Kong
    ".AX":   0.30,    # Australia
    ".NZ":   0.28,    # New Zealand
    ".SI":   0.17,    # Singapore
    ".KS":   0.275,   # Korea KOSPI (incl. local surtax)
    ".KQ":   0.275,   # Korea KOSDAQ
    ".TW":   0.20,    # Taiwan
    ".TWO":  0.20,    # Taiwan OTC
    # Asia EM
    ".NS":   0.25,    # India (effective; concessional new regime)
    ".BO":   0.25,    # India
    ".SS":   0.25,    # China A-shares (Shanghai)
    ".SZ":   0.25,    # China A-shares (Shenzhen)
    ".JK":   0.22,    # Indonesia
    ".BK":   0.20,    # Thailand
    ".KL":   0.24,    # Malaysia
    # Americas non-US
    ".TO":   0.265,   # Canada — federal + provincial blended
    ".V":    0.265,   # Canada — TSX Venture
    ".SA":   0.34,    # Brazil — IRPJ + CSLL combined
    ".MX":   0.30,    # Mexico
    # Other emerging
    ".JO":   0.27,    # South Africa
    ".SR":   0.20,    # Saudi Arabia
    ".IS":   0.25,    # Turkey
}

# Region-level fallback for tax rate when suffix is unknown — kept for
# backward compatibility and as the last-resort default.
DEFAULT_MARGINAL_TAX_RATE = {
    "US":         0.21,
    "UK":         0.25,
    "EUROZONE":   0.25,
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


def get_defaults(region: str, suffix: str | None = None) -> dict:
    """Return all WACC-input defaults for a ticker.

    ``region`` drives ERP and country risk premium (broad regional defaults).
    ``suffix`` (Yahoo-style, e.g. ``".DE"``, ``".HK"``, ``""`` for US) drives
    the marginal tax rate at country level. If ``suffix`` is None or unknown,
    the marginal tax rate falls back to the regional default for ``region``,
    which itself falls back to ``OTHER`` for unknown regions.
    """
    fallback = "OTHER"

    # Tax: prefer country-specific rate, then regional, then OTHER
    tax = None
    if suffix is not None:
        tax = MARGINAL_TAX_BY_SUFFIX.get(suffix)
    if tax is None:
        tax = DEFAULT_MARGINAL_TAX_RATE.get(region, DEFAULT_MARGINAL_TAX_RATE[fallback])

    return {
        "equityRiskPremium":  DEFAULT_ERP.get(region,                  DEFAULT_ERP[fallback]),
        "marginalTaxRate":    tax,
        "countryRiskPremium": DEFAULT_COUNTRY_RISK_PREMIUM.get(region, DEFAULT_COUNTRY_RISK_PREMIUM[fallback]),
    }
