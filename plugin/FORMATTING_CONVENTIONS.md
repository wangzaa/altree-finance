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
