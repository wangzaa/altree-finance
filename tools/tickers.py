"""Ticker parsing, region inference, and directory-name mapping.

Pure logic. No I/O. No external dependencies.

Yahoo Finance suffixes use periods (e.g. ``7203.T``, ``BARC.L``). Filesystem
directory names replace the period with an underscore (``7203_T``, ``BARC_L``)
so that shell globbing and tooling stays clean. The original ticker string
is preserved inside ``summary.json.ticker``; the directory naming is one-way
(canonicalize on save, never reverse).
"""

REGION_BY_SUFFIX = {
    "":      "US",
    ".L":    "UK",
    ".PA":   "EUROZONE",
    ".DE":   "EUROZONE",
    ".AS":   "EUROZONE",
    ".MI":   "EUROZONE",
    ".MC":   "EUROZONE",
    ".T":    "JAPAN",
    ".HK":   "ASIA_DM",
    ".AX":   "ASIA_DM",
    ".SI":   "ASIA_DM",
    ".NS":   "ASIA_EM",
    ".BO":   "ASIA_EM",
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
