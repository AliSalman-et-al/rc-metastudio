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

Each table has a required closed semantic role supplied by its R producer and
validated by the bridge and immutable Python contract. Executed metric, workflow,
inference codes and layout accompany that role. Titles and column headings remain
display text; missing or unknown roles fail the boundary. Supporting output stays
supporting even when its columns resemble pooled effects or coefficients.
Quantified arrays require an explicit producer role before request attachment;
the owned converter may label unquantified, display-only named output supporting.
Retention preserves source rows whose study counts, group or prediction context
are not fully represented by a primary summary; equal numbers alone do not prove
that two tables describe the same result.

The synchronous bridge converts a frozen analysis model and executes its request
within one serialized call, passing the converted R object explicitly. Method
discovery owns a separate explicit object. Plot regeneration retains its existing
saved-object contract. Executed fits supply authority-package versions and actual
inference codes. Setup constructs the pure report, identity and rerun snapshot
before accepting and delivering the result once; preparation errors leave setup
open and preserve the previous result.

## Result normalization

Named R character vectors can represent an estimate and interval. Render the
fields as a structured estimate so each value survives. A named R container
can render into multiple sections. Keep the container's semantic title on
the first rendered child while preserving the one-section-per-value contract.
The one-study path unwraps its technical MAResults transport container before
assigning headings.

Data frames can reach the bridge as column vectors, while matrices can carry a
flat column-major vector. Both describe the same dimensions. Normalize the
shape before indexing. Percentile headings already carry display punctuation
and bypass identifier normalization. For combined diagnostic requests, carry
the chosen subgroup on every filtered request independently of each method's
parameter list.

Normalize text identifiers with the same rules in section headings and nested
display values. Pad missing cells in a partially populated display matrix so
the available results can still be read. The exact quantity contract continues
to validate the declared dimensions.
