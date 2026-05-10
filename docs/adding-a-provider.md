# Adding a new open-source data provider

This fork's "layered light fork" structure keeps data-source policy
centralized. Adding a new provider should NOT require touching SKILL.md
files or command files.

## Recipe

1. **Confirm the provider is open-data.** Government/central-bank/IGO data
   is fine. Free-tier commercial APIs (FMP, Polygon, Tiingo free) are NOT
   in scope for this fork.

2. **Add a sub-section to `docs/providers/<name>.md`** documenting:
   - What the provider covers
   - What we trust it for (and what we don't)
   - Version pinning notes
   - Known failure modes

3. **Wire the call into `tools/shared.py` (for shared data) or
   `tools/fetch.py` (for ticker-scoped data).** Use OpenBB if the provider
   is wrapped there; otherwise add a direct `requests.get(...)` call.
   Always probe the actual API surface first:
   ```python
   from openbb import obb
   import inspect
   print(inspect.signature(obb.economy.SOMETHING))
   r = obb.economy.SOMETHING(provider="new_provider")
   print(sorted(r.results[0].model_dump().keys()))
   ```

4. **Extend `tools/normalize.py` to merge the new provider's fields into
   `summary.json`.** Update the schema doc in `docs/data-schema.md` and
   add a citation source string for each new numeric field.

5. **Add unit tests in `tests/test_normalize.py`** if the new fields go
   through transformation logic. Pure-data fields (like `_shared/` series)
   don't need unit tests; integration verification via end-to-end smoke
   runs is sufficient.

6. **Update `DATA_CONVENTIONS.md`** if the new provider changes any
   workflow rules visible to skills (it usually shouldn't).

7. **Do NOT modify any SKILL.md or command file.** Skills read
   `summary.json`; if the schema is the same, skills don't need to know
   the new provider exists.

## What you should NOT do

- Add an MCP server. This fork is intentionally MCP-free.
- Add a paid-tier API key requirement.
- Add a provider that conflicts with another one's domain ownership in
  `summary.json` (each leaf field should have exactly one owning source).
