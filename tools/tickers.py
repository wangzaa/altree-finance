"""Ticker parsing, region inference, and directory-name mapping.

Pure logic. No I/O. No external dependencies.

Yahoo Finance suffixes use periods (e.g. ``7203.T``, ``BARC.L``). Filesystem
directory names replace the period with an underscore (``7203_T``, ``BARC_L``)
so that shell globbing and tooling stays clean. The original ticker string
is preserved inside ``summary.json.ticker``; the directory naming is one-way
(canonicalize on save, never reverse).
"""

REGION_BY_SUFFIX = {
    # United States
    "":      "US",

    # United Kingdom
    ".L":    "UK",          # London Stock Exchange (main)
    ".IL":   "UK",          # International order book / ETF quotes

    # Eurozone — primary national exchanges
    ".PA":   "EUROZONE",    # Paris Euronext (France)
    ".DE":   "EUROZONE",    # Xetra (Germany)
    ".F":    "EUROZONE",    # Frankfurt (Germany, alternative)
    ".AS":   "EUROZONE",    # Amsterdam (Netherlands)
    ".MI":   "EUROZONE",    # Milan (Italy)
    ".MC":   "EUROZONE",    # Madrid (Spain)
    ".BR":   "EUROZONE",    # Brussels (Belgium)
    ".LS":   "EUROZONE",    # Lisbon (Portugal)
    ".HE":   "EUROZONE",    # Helsinki (Finland)
    ".VI":   "EUROZONE",    # Vienna (Austria)
    ".IR":   "EUROZONE",    # Dublin (Ireland)
    ".AT":   "EUROZONE",    # Athens (Greece)

    # Developed Europe non-Eurozone — mapped to EUROZONE defaults as the
    # closest fit (tax rates differ; user can override with --tax-rate)
    ".SW":   "EUROZONE",    # SIX Swiss Exchange (Switzerland)
    ".OL":   "EUROZONE",    # Oslo (Norway)
    ".ST":   "EUROZONE",    # Stockholm (Sweden)
    ".CO":   "EUROZONE",    # Copenhagen (Denmark)

    # Japan
    ".T":    "JAPAN",       # Tokyo Stock Exchange

    # Asia — Developed
    ".HK":   "ASIA_DM",     # Hong Kong Exchanges
    ".AX":   "ASIA_DM",     # Australia (ASX)
    ".NZ":   "ASIA_DM",     # New Zealand (NZX)
    ".SI":   "ASIA_DM",     # Singapore (SGX)
    ".KS":   "ASIA_DM",     # Korea KOSPI
    ".KQ":   "ASIA_DM",     # Korea KOSDAQ
    ".TW":   "ASIA_DM",     # Taiwan Stock Exchange
    ".TWO":  "ASIA_DM",     # Taipei OTC

    # Asia — Emerging
    ".NS":   "ASIA_EM",     # India (NSE)
    ".BO":   "ASIA_EM",     # India (BSE)
    ".SS":   "ASIA_EM",     # Shanghai A-shares (China)
    ".SZ":   "ASIA_EM",     # Shenzhen A-shares (China)
    ".JK":   "ASIA_EM",     # Jakarta (Indonesia)
    ".BK":   "ASIA_EM",     # Bangkok (Thailand)
    ".KL":   "ASIA_EM",     # Kuala Lumpur (Malaysia)

    # Americas — non-US (developed and emerging)
    ".TO":   "OTHER",       # Toronto (Canada, developed; defaults closer than US tax)
    ".V":    "OTHER",       # TSX Venture (Canada)
    ".SA":   "OTHER",       # B3 (Brazil)
    ".MX":   "OTHER",       # Mexico

    # Other emerging — broad bucket
    ".JO":   "OTHER",       # Johannesburg (South Africa)
    ".SR":   "OTHER",       # Saudi Tadawul
    ".IS":   "OTHER",       # Borsa Istanbul (Turkey)
}


def parse_ticker(ticker: str) -> dict:
    """Parse a Yahoo-style ticker into its components.

    Returns a dict with keys: ``ticker`` (original), ``suffix`` (e.g. ``.T``
    or empty string), ``region`` (one of the values in ``REGION_BY_SUFFIX``,
    or ``"OTHER"`` for unknown suffixes), and ``dir_name`` (filesystem-safe).
    """
    if "." in ticker:
        idx = ticker.index(".")
        suffix = ticker[idx:]
    else:
        suffix = ""
    region = REGION_BY_SUFFIX.get(suffix, "OTHER")
    return {
        "ticker":   ticker,
        "suffix":   suffix,
        "region":   region,
        "dir_name": ticker.replace(".", "_"),
    }


def to_dir_name(ticker: str) -> str:
    """Convert a ticker to its filesystem-safe directory name."""
    return ticker.replace(".", "_")


def region_for(ticker: str) -> str:
    """Convenience wrapper returning just the region for a ticker."""
    return parse_ticker(ticker)["region"]
