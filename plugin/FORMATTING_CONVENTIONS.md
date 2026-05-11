# Formatting conventions (Excel outputs)

Excel (.xlsx) outputs from this fork's skills follow a fork-wide formatting
convention. Skills MUST apply these defaults unless the user supplies a
template or an explicit style override.

## Default font

- **Family**: `Arial`
- **Size**: `10` (pt)

This overrides:
- openpyxl's library default (Calibri 11pt)
- The "Suggested Font & Typography" defaults in upstream `comps-analysis`
  (Times New Roman 11/12pt) — those are explicitly superseded for this fork

## Color palette (unchanged from upstream)

- **Blue** (`#0000FF`) — hardcoded inputs / assumption drivers
- **Black** — formulas
- **Green** (`#008000`) — cross-sheet / cross-file links

## How to apply (openpyxl)

Every `Font(...)` constructor MUST include `name="Arial", size=10`
alongside any color/bold attributes:

```python
from openpyxl.styles import Font

# Hardcoded input — blue
ws["C2"].font = Font(name="Arial", size=10, color="0000FF")

# Formula — black (default color)
ws["C5"] = "=Inputs!C2*(1+Inputs!C3)"
ws["C5"].font = Font(name="Arial", size=10)

# Cross-sheet link — green
ws["D5"].font = Font(name="Arial", size=10, color="008000")

# Section header — Arial 10pt bold + fill
ws["A1"].font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
ws["A1"].fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
```

For cells written WITHOUT an explicit `.font` assignment, openpyxl falls
back to Calibri 11pt — so apply `Font(name="Arial", size=10)` to every cell
you write, even for plain black formulas. There is no clean openpyxl API
for "workbook-wide font default"; per-cell application is the rule.

## Header sizes

Headers stay at the same 10pt size — use **bold** + fill color for
emphasis, not larger font sizes. This keeps the model dense and readable
on standard zoom (100%).

## When NOT to apply this

- User uploads a template with its own existing styling — preserve the
  template's font/sizing, do not impose Arial 10pt on top.
- User explicitly requests a different font or size for a specific
  deliverable.
- Output is a `.pptx` deck (this convention is Excel-only; slides have
  their own typography).

## Notes & Methodology cells — overflow, not wrap

Every model produced by this fork MUST include a **Notes & Methodology**
section (own tab or clearly-delimited block at the bottom of the main
sheet). Text in this section must be set to **overflow** (Excel default),
NOT wrap. Reasons: wrapped text inflates row heights inconsistently,
breaks visual alignment, and makes long source citations harder to scan.

```python
from openpyxl.styles import Alignment
ws["A1"].alignment = Alignment(wrap_text=False, horizontal="left", vertical="top")
```

Do NOT set `wrap_text=True` on Notes & Methodology cells. Let long
strings overflow across adjacent empty cells per Excel's default
behavior. Row height stays uniform; readers widen the column or click
into the cell to see the full text.

## What goes in Notes & Methodology

Document everything an auditor would need to reproduce or challenge the
model. Required content, at minimum:

1. **Data source summary** — list of `source` strings from `summary.json`
   used in the model, with their fetch date.
2. **Currency handling** — for any multi-currency comp set, state the
   currency policy explicitly. If the comp table is multiples-only,
   state that and explain why (avoids cross-currency conversion error).
3. **Currency idiosyncrasies / data quirks** — explicit call-outs for
   anything unusual in the source data. Examples:
   - `BA.L` reports `currency: "GBp"` (pence) but `marketCap` is in GBP;
     do not multiply by 100.
   - Yahoo's `fiscal_year` field is `null` for yfinance-sourced
     fundamentals; year derived from `period_ending` date.
   - Risk-free rate for ASIA_DM region falls back to US 10Y CSV; cited
     source string flags this explicitly.
4. **WACC assumptions** — risk-free rate, ERP, beta, country risk
   premium, marginal tax rate, each with its `source` string and any
   manual override (e.g. `--tax-rate 0.30` for Germany).
5. **Projection assumptions** — growth rates, margin trajectory, capex
   intensity, terminal value method, with explicit user-supplied vs
   derived classification.
6. **Known limitations** — list anything the model can't fully address:
   missing peers in regional categories, stale macro data dates, etc.

Notes & Methodology is the model's audit trail. Do not skip it.
