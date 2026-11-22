# Verification lanes

## Native and typing commands

Follow [native and typing commands](../../../../docs/maintaining.md#native-and-typing-commands) and [verification lanes](../../../../docs/maintaining.md#verification-lanes-and-test-suites) for prerequisites and gate selection.

Focused source behavior with native rendering can use:

```powershell
uv run python scripts/verify_rcms.py amino --native
```

For specific native evidence, the maintained scripts include:

```powershell
uv run python scripts/native_calculator_smoke.py
uv run python scripts/native_calculator_smoke.py --validate-only
uv run python scripts/native_results_smoke.py
uv run python scripts/native_results_smoke.py --validate-only
uv run python scripts/native_remaining_surfaces_smoke.py
uv run python scripts/native_remaining_surfaces_smoke.py --validate-only
```

Calculator and Results evidence defaults to `build/qt6-verification/native-calculators` and `native-results`; these are shared output directories. Do not run overlapping native probes concurrently in one checkout. Preserve their output under the current proof directory before cleaning build outputs. Native RemainingSurfaces supports `--evidence-root`; use a unique destination when invoking it directly.

## Numerical and release scope

Frozen comparison covers 11 cases (three basic plus eight binary/continuous extended). The authority script supplies 103 independent public-package comparisons plus effect reconstruction assertions, including single/double-zero correction policies. Current-source R-stack supplies joint Reitsma public-`mada` comparisons and 21-case visual QA. These complement one another; none alone proves all UI modes. Small-study numerical gaps and mandatory targeted recipes are in its feature map.

After a golden-comparator-only correction, preserve the original failed report and re-run that gate without repeating already-passed unchanged package tests. For a configured warm Windows runtime:

```powershell
$env:R_HOME = $env:RCMS_R_HOME
$env:R_LIBS = $env:RCMS_R_LIBS
$env:R_LIBS_USER = $env:RCMS_R_LIBS
$env:PATH = "$env:R_HOME/bin/x64;$env:R_HOME/bin;$env:PATH"
uv run python scripts/verify_golden_compatibility.py --root . --output-root build/qt6-verification/golden-compatibility-targeted
```

The golden CLI needs that R environment explicitly; the desktop helper configures its bootstrap itself. Verify the saved `compatibility-report.json`, all 416 numerical fields and plot contracts, and identify the selected library/source provenance. Text comparison canonicalizes a line-leading heterogeneity `t²`/`τ²` header before Q. Scoped exceptions also bind exact before/after text or the documented scale and Greek-label corrections; they preserve scientific tokens and numbers. Changed numbers, unrelated narrative and other text still fail. Frozen contracts and tolerances remain unchanged. A focused recovery pass does not retroactively make the original failed full-run command successful; report its failed stage and the corrected gate's evidence.

See the [release guide](../../../../docs/release.md) for package qualification. R dependency identity comes from `config/r-dependencies.json`, not remembered latest versions. ADR-0001 delegates statistical decisions to the authority packages. Golden tolerance changes require justification independent of current output.

Release targets are Windows x64, Apple silicon macOS, and Ubuntu 24.04 x86_64 (ADR-0009). A local Windows proof cannot qualify the other targets. Exact artifact hashes, relocatability, runtime provenance, platform trust and release-set evidence come from package qualification. This skill does not authorize publishing, promotion, signing, workflow dispatch, or messaging others.

### Native layout evidence identity and retries

Adaptive-layout evidence includes a current-source digest, a run ID and an
`invocation.json` receipt. The validator requires matching receipt/manifest
identity plus table, splitter, geometry round-trip and actual resize observations.
It accepts Windows x64 and Apple Silicon macOS architecture names only for their
respective targets. Older bundles without these records must be recollected.
Starting another attempt archives prior captures beside the output directory;
startup failure cannot leave an earlier manifest presented as the new result.

Remaining-surfaces evidence requires both scales to share platform, run and
source identity. Each scale uses a fresh fragment directory; retries retain
fragments and archive previous scale captures under `.previous-attempts`.
The covariate Cancel probe edits the real conversion model through the owning
MainWindow and checks covariate definitions and every row's values after rejection.
Native Results smoke drives Edit and Export through their QActions, observes a
committed caption and image, and hashes the exported SVG. Its renderer is a
controlled fixture, so this lane does not qualify statistical fitting.

The UX scenario snapshots/restores clipboard MIME bytes in `finally` and seeds
owned content before exercising Copy. It never records the prior clipboard.
The clipboard GUI cases also restore MIME data; sentinel failure tests run only
with the offscreen clipboard. The fractional-scale workspace child sets its own
INI settings path before startup and reports that path for containment checking.
Offscreen screen descriptors and rendered captures cannot establish native
multi-monitor placement or native DPI behavior.

### Import progress completion evidence

The remaining-surfaces collector records close and Escape rejection while CSV
import owns the modal dialog, followed by owner completion through `hide_once`.
It requires all three observations; closing import progress is not cancellation.

### QA audit contracts

The standalone forest matrix writes its manifest before returning failure when any
render fails. Footer CLI checks remain active under Python optimization, including
the shared geometry observer. Optional visual tests must not change the caller's
output-root environment.

Formatting captures retain malformed array members with source/index diagnostics.
The Qt ownership audit counts direct initializer registration (or the explicitly
called `_configure_window` step), not calls in dead branches or uncalled methods.
This is a narrow static contract, not proof of runtime native ownership.

Native calculator bundle validation requires exactly the three successful Windows
transactions, their model outcomes and intact captures. The analysis smoke checks
the exact selected backend request and typed owner delivery; its explicit backend
fixture does not establish live R numerical correctness.


## Reporting

State the behavior proved and link its evidence directory. Include commands, runtime/platform, pass/fail and material skip reasons. If a path was unavailable, name the attempted action and missing precondition. Do not report a release qualified from source tests, a skipped path as passed, or a success marker from a process that crashed afterward.
