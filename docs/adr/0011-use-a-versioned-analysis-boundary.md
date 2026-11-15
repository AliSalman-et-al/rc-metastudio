# Use a versioned analysis boundary

Python and RCMetaR exchange immutable requests and versioned structured results whose stable identifiers and kinds control application behavior. Human-facing titles remain presentation only, trading a deliberate boundary schema for freedom to change wording and layout without changing result semantics.

Result tables may carry per-cell quantities alongside producer display strings:
role, exact double or missing value, analysis/display scale and interval level in
percent. Combined display cells can retain several quantities. Numeric routing
uses these roles; exports never reconstruct precision from text. R attaches the
quantities to its display arrays and the bridge validates them before use.

This additive field remains in version 1. Results are not persisted in projects,
and the Python and RCMetaR producers are qualified together. A table without
quantities is formatted output only; there is no text-parsing compatibility path.
