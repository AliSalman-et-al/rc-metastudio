# Round 3 verification

All commands run from `/home/ali/Documents/Code/rc-metastudio` using the locked
Python 3.11.9 environment and real R 4.6.1. `TEST-RUNS.json` retains exact argument
arrays, environment, revision, timestamps, exit status and raw-log SHA-256 for
every recorded attempt. Raw logs remain ignored. Desktop manifests additionally
bind dirty source, harness, runtime, inputs, action snapshots and artifact bytes.

## Pinned, test-owned Linux setup

System R 4.3.3 was not used for analysis or package installation. The private
runtime is `build/ux-round3/r-home`, with a separate persistent library
`build/ux-round3/r-library`. [RUNTIME.json](RUNTIME.json) records archive and
launcher hashes, the observed native runtime and the pinned authority versions.

Setup used these commands and the relocation block from
`scripts/build-linux-package.sh` (the `Making Posit R launchers relocatable`
Python block). Every destination is test-owned:

```bash
uv sync --locked
mkdir -p build/ux-round3/runtime-cache build/ux-round3/runtime-extract
curl --fail --location --retry 3 https://cdn.posit.co/r/ubuntu-2404/pkgs/r-4.6.1_1_amd64.deb --output build/ux-round3/runtime-cache/r-4.6.1_1_amd64.deb
sha256sum build/ux-round3/runtime-cache/r-4.6.1_1_amd64.deb
dpkg-deb -x build/ux-round3/runtime-cache/r-4.6.1_1_amd64.deb build/ux-round3/runtime-extract
cp -a build/ux-round3/runtime-extract/opt/R/4.6.1/lib/R build/ux-round3/r-home
```

R archive SHA-256:
`5af816371126c8e5895600de035153cd3a64b12f4beb43f291ee34bf24f8fd2d`.
After applying the relocation block, replace only the private Rscript wrapper
with [Rscript.sh](Rscript.sh). The packaging wrapper forwarded positional script
arguments but dropped trailing arguments after `-e`; the retained wrapper handles
both cases. The original compiled launcher cannot use this relocated R home.

The native Qt prerequisite came from the packaging script's pinned Noble archive:

```bash
curl --fail --location --retry 3 https://archive.ubuntu.com/ubuntu/pool/universe/x/xcb-util-cursor/libxcb-cursor0_0.1.4-1build1_amd64.deb --output build/ux-round3/runtime-cache/libxcb-cursor0_0.1.4-1build1_amd64.deb
sha256sum build/ux-round3/runtime-cache/libxcb-cursor0_0.1.4-1build1_amd64.deb
dpkg-deb -x build/ux-round3/runtime-cache/libxcb-cursor0_0.1.4-1build1_amd64.deb build/ux-round3/xcb
source docs/ux-audit/2026-10-14-round3/ENV.sh
```

Cursor archive SHA-256:
`137cf52479b5a9d8c5926d70d311af04be41941a32ee777340d704cc458c06d8`.
No system package installation was performed. Private symlinks in
`build/ux-round3/link-libs` expose the already installed versioned libdeflate,
libzstd and libtirpc to the linker; [RUNTIME.json](RUNTIME.json) records their
resolved paths. The successful API-bridge build used `LIBRARY_PATH`, after the
initial missing-API-module and linker failures:

```bash
LIBRARY_PATH="$PWD/build/ux-round3/link-libs" RPY2_CFFI_MODE=API uv pip install --python .venv/bin/python --no-cache --no-deps --reinstall --no-binary rpy2-rinterface rpy2-rinterface==3.6.6
RCMS_POLICY_PYTHON="$PWD/.venv/bin/python" "$RCMS_R_HOME/bin/Rscript" scripts/install-r-deps-linux.R "$PWD" "$RCMS_R_LIBS" "$PWD/build/ux-round3/package-archives"
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
uv run python docs/ux-audit/2026-10-14-round3/install_source.py
uv run python scripts/verify_rcms.py doctor --native
```

Exit status: 0 for the successful setup, source installation, generated forms and
native doctor. The dependency installer validates the dated Noble `4.6-noble`
binary policy and exact pinned authority versions; source fallback is disabled.
No qualified package was modified. Current-source provenance is
[INSTALLED-SOURCE.json](INSTALLED-SOURCE.json), including source/archive/installed
tree hashes. Each native runtime observes `xcb`, Qt 6.11.1, PyQt 6.11.0, rpy2 3.6.7,
RCMetaR 0.4.2 and the selected private library.

## Numerical and golden gates

```bash
uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh  # includes strict golden capture
uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-r-stack-v2
"$RCMS_R_HOME/bin/Rscript" .agents/skills/verify-rcms/scripts/analysis_authorities.R docs/ux-audit/2026-10-14-round3/raw/authorities.json
```

Exit status: 0, 0, 0. The final full profile supplies the strict golden and public
authority captures; the standalone authority command also passed. Golden capture: 11 cases, 461 passing comparisons and
13 existing accepted exceptions. Every one of the 415 original numerical fields
is exactly equal, maximum absolute difference 0. The retained numeric-policy rows
are identical to the pre-round contract. Public authority matrix: 91 cases pass.
See [NUMERICAL-EQUIVALENCE.json](NUMERICAL-EQUIVALENCE.json).

Earlier golden failures exposed intentional text changes and newly displayed
continuous subgroup fields. New fields are now retained separately, independently
verified, and cannot replace original oracle fields. Six report-text sections were
reviewed before the sanctioned `scripts/regenerate_golden_presentation.py` refresh;
only text and archive SHA bindings changed. Numerical oracles, tolerance rows and
exceptions were never regenerated.

## Required full profile and forest matrix

```bash
uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh
RCMETASTUDIO_QA_ROOT="$PWD/artifacts/verification/rcms/round3-forest-dx" "$RCMS_R_HOME/bin/Rscript" r/RCMetaR/inst/qa/render_forest_visual_qa.R
```

The final uncached full profile exits 0 (`raw/full-dx.json`, 1,835.012 seconds),
from commit `273bd6a`, including the final `70b996c` spacing fix. Its desktop
lane reports `98 passed in 1213.68s (0:20:13)`. R CMD check reports `Status: OK`,
with no NOTE; its testthat transcript records `FAIL 0 | WARN 2 | SKIP 1 | PASS 1817`.
The skipped optional 300-case R-test gallery is supplied by the separate maintained
matrix. `FULL-PROFILE.json` binds all 98 unique fresh offscreen manifests plus
doctor to the complete registry, runtime, actions and artifact hashes. Nine R-stack
tests passed in 68.65 seconds; both 21-case Reitsma render lanes, strict golden
checks and 91 public authority comparisons passed. Every original field remains
exactly equal. No scenario timed out. HR/IRR/subgroup exports remain within their
original 600/600/240-second budgets (198.27/217.81/74.16 seconds under concurrency).

The earlier successful `039ef01` full profile (`raw/full-packed.json`) took
2,869.713 seconds including first qualification of the changed dependency-cache
key; its serial desktop lane took 1,936.99 seconds. These are single observed
runs with different concurrent load/cache state, not a controlled speedup study.
The interrupted final-source repeat (`raw/full-final.json`, exit 1) was stopped
at the user's request to improve DX; it is not represented as a passing command.

The final gallery (`raw/forest-dx.json`) exits 0 in 237.436 seconds while running
at reduced CPU priority alongside the end of qualification. Its full decoding/SVG
check exits 0 in 20.770 seconds: 300 unique cases, no manifest errors, visible
nonwhite content and retained canonical SVGs; previews have maximum edge 2,400.
`FOREST-MATRIX.json` retains every dimension and hash. The earlier gallery did not
retain canonical SVGs, so the planned exact old/new vector comparison cannot be
established. No such equality or controlled gallery speedup is claimed.

The earlier full run is retained at
`artifacts/verification/rcms/20261014T055617Z-382d3481-complete`: exit 1,
`8 failed, 90 passed`. R CMD check passed with one NOTE about the existing `tiff`
Imports declaration. Bridge, nine R-stack tests and both 21-case Reitsma renders
passed. Its package was built before the final journal-axis and small-SE changes,
so it is not final-source proof.

## Native proof

```bash
source docs/ux-audit/2026-10-14-round3/ENV.sh
bash docs/ux-audit/2026-10-14-round3/NATIVE.sh native-dx
uv run python docs/ux-audit/2026-10-14-round3/curate.py native-dx
```

All twelve targeted native scenarios pass: the eight original dataset families,
HR, IRR, public subgroup/diagnostic references, and precision. Each family exercises
cumulative, omission and subgroup paths where supported. Assertions compare
actual report rows with SVG text at the same vertical coordinate, rather than
trusting fit positions. Subgroup comparisons use public package refits; new PIs
are package predictions only, with existing applicability rules.

`OBSERVATIONS.json` retains commands, original manifests/runtime and all observed
rows, public references and copied/exported text. `SCREENSHOTS.json` binds the
curated native PNGs to original captures. Every screenshot cited in CHANGES has
been visually inspected. The HR example has many rows and therefore requires
scrolling; complete row proof comes from SVG/report comparisons, not a cropped
native viewport. Native drives control the file picker destination; they do not
prove OS picker behavior, fractional DPI, accessibility or release qualification.

## Failures and corrections

Failure attempts remain in ignored `raw/` and their desktop evidence directories.
`TEST-RUNS.json` records exact commands/status/log hashes for every attempt.

- Startup: missing rpy2 API module, then missing linker names for already installed
  versioned libraries; fixed in the owned Python/runtime setup described above.
- Native startup: missing libxcb-cursor; fixed with the pinned private extraction.
- Rscript `-e` lost trailing positional arguments; fixed only in its private wrapper.
- Initial R check failures: callers/tests still assumed positional overall fits or
  obsolete header/tick behavior. They were migrated/deleted with the old design.
- One combined audit exceeded its 600-second limit; replaced with fresh-process
  family drives rather than weakening assertions.
- Premature viewport assertions ran before queued native resize/refit completed;
  the driver waits for the production queue to settle.
- An interrupted full run collided with another cleanup of the same owned cache.
  The recorded owned process tree was stopped, its partial cache retained, and the
  verified pinned private dependency library restored. One full run owns its cache installation; offscreen cases now use bounded independent workers.
- Missing journal null tick: the line existed, but metafor suppressed the zero label
  because an endpoint label overlapped. Shared spaced axis ticks now render it.
- Precision fixture first edited an estimate against old bounds; it now clears the
  old cells first. Bubble coverage first divided by canvas height; it now uses the
  actual circle group's plotting-frame clip rectangle. Neither fix changes output.
- Old copy-report assertion expected the screen serialization. It now checks the
  executed identity, complete table rows, shortcut/action equality and disk export.
- Old HR/IRR authority checks expected `+ Study`/`- Study`; migrated to the new roles.
- Small SE was genuinely lost. Reproduced before its fix:

```text
AssertionError: ('0.000000', 4.082482904638632e-12)
```

The corrected native report preserves `4.082483e-12`; public fit and original
golden/equivalence gates pass. Other representative failure messages, verbatim:

```text
KeyError: 'model.through_study_1.estimate'
UNEXPECTED DIALOG: The lower CI must be less than the point estimate!
AssertionError: ([(0.135, 248.65), (0.368, 190.66), (1.0, 132.67), (2.718, 74.67)], 360.0)
AssertionError: {'range': [0.5, 2], 'null': 0}
```

The last message came from the harness calling the refline helper without its
explicit limits; the actual edited SVG already omitted the line. The corrected
drive checks both persisted limits and the real SVG.

The earlier full run timed out in the entered-continuous calculator and the
subgroup plot editor. Its exact timeout messages and all eight failed test IDs
are retained verbatim in `EARLIER-FULL-FAILURES.json`. The entered-continuous calculator passed an unchanged retry in
12 seconds; no timeout limit or production calculation was changed.

## Additional checks and limits

```bash
uv run python -m pytest --strict-markers tests --collect-only -q
uv run ty check --extra-search-path build/qt6-verification/generated/rc_metastudio --extra-search-path build/qt6-verification/generated/rc_metastudio/forms --extra-search-path . --extra-search-path src/rc_metastudio --extra-search-path src --extra-search-path scripts --extra-search-path tests/python/gui src/rc_metastudio/analysis_identity.py src/rc_metastudio/analysis_setup_dialog.py src/rc_metastudio/results_window.py tests/e2e/audit_round3.py tests/e2e/ux_workflows.py
```

Exit status: 0 and 0. The unconfigured repository-wide `ty check` first returned
94 diagnostics, including missing generated paths and PyQt static-method stubs.
The configured repository-wide lane first returned 16: four R-object indexing
issues (corrected with the existing bridge decoder) plus Linux-unavailable Windows
`pefile`/`winreg` imports. Its final retry returned 12 Windows-only diagnostics. The changed-file strict lane is green. The broad Windows
type lane is not established on this Linux host and is not a release-package claim.

## User-requested performance work

See [BENCHMARKS.md](BENCHMARKS.md) for exact alternating commands, medians, ranges,
peak RSS, independent decoded-pixel comparisons and limits. The old and new
converter both run against `TIFF-input.svg`; all ten runs exit 0. The transparency
fixture exits 0 (43 checks). HR, IRR and subgroup editor/export drives exit 0.
The IRR attempt before its year-aware non-estimable-row assertion correction
failed, verbatim:

```text
AssertionError
```

The assertion expected `Study 1 (k = 1)`, while the actual report and non-estimable
section correctly said `Study 1, 2020 (k = 1)`. Its fresh retry passed all public
references and 24 decoded exports with the original 600-second timeout.

Small-effect geometry was caught during visual review. The first strengthened
drive exposed a missing harness import (`NameError: name 're' is not defined`).
After correcting the harness, the pre-fix figure failed, verbatim:

```text
AssertionError: {'8.00e-11'}
```

After scaling by the real effect range and measuring sparse columns, the native
drive passes and shows five ticks, six visible intervals and readable labels.
The retained precision screenshot is from the passing final source. No statistical
fit, reported stored number, or numerical tolerance changed.

A broadened type check over existing skill drivers returned 19 diagnostics from
pre-existing Qt-stub overloads and driver globals. The strict changed product/audit
file lane remains the established type proof; broader platform/stub qualification
is not claimed. Exact attempt commands and messages remain in TEST-RUNS.

The earlier successful serial full profile completed the formerly blocking HR and IRR editor drives
in 101.61 and 124.79 seconds, and subgroup editor/export in 48.91 seconds, within
the original 600/600/240-second limits. No scenario timed out. All 98 fresh-process
artifacts bind to commit `039ef01`. The 91 authority cases passed; final numerical
equivalence has maximum difference 0 across every original field.

The last native spacing failure was reproduced before its two-coordinate fix:

```text
AssertionError: ('weight/estimate gap', -7.534999999999968)
```

The strengthened real drive measures the emitted SVG's text lengths and anchors
for every ordinary-scale weight/estimate pair. After the measured-block offset
fix it passes, and both ordinary and genuinely small figures have clear columns.
The final fresh `273bd6a` profile includes `70b996c` and passes every required gate; the previous passing `039ef01` profile remains separately recorded.

## Complete warm feedback loop and bounded execution

```bash
uv run python -m pytest tests/e2e -n auto --fresh -k analysis-data-onearm-mean  # taskset -c 0 for the observed one-CPU drive
uv run python docs/ux-audit/2026-10-14-round3/verify_resume.py
uv run python .agents/skills/verify-rcms/scripts/verify_all.py
uv run python docs/ux-audit/2026-10-14-round3/collect_warm_profile.py
```

The constrained CPU drive exits 0, selects one worker and runs a fresh real Qt/R
case. The mixed six-case pilot exits 0 with three workers, including 24 HR exports
and subgroup exports. `DX-RESUME.json` proves five intact-evidence validations,
fresh reruns for changed source/startup configuration and damaged/missing images,
and no cache entry after an intentionally failing forms-root startup.

The complete warm matrix exits 0 in **35.438 seconds**, including signature
calculation, all 98 cases and a fresh doctor. `DX-WARM-PROFILE.json` independently
checks all 98 cache pointers, original full-profile manifest hashes and every
artifact hash. It explicitly records reuse rather than claiming 98 new fits.
A selected warm case passed in 2.77 seconds of pytest time (19.186 seconds including
signature calculation under concurrent qualification/gallery load).

A fresh source installation embeds different build-path bytes. The active full
lane's exact installed library was retained under
`build/ux-round3/r-stack-retained-273bd6a` and verified file-for-file. `ENV.sh`
selects it for warm driving. `INSTALLED-SOURCE.json` records this retained current
source installation; `NATIVE-INSTALLED-SOURCE.json` retains the earlier persistent
installation used by the twelve native captures. Both use the same current R
source. Qualified dependency bytes were copied unchanged. No runtime comparison
was weakened to ignore executable namespace or bytecode differences.

The new helper/resource files pass strict Ty; strict test collection exits 0
with 1,014 cases. Changed product/audit strict Ty remains green. Artifact metric
comparison exits 0 with 27 exactly equal dictionaries (26 final PNGs plus blank).
`VISUAL-REVIEW.md` records inspection of all 26 final native captures.

The first offline `uv lock` attempt failed, verbatim:

```text
error: No solution found when resolving dependencies for split (markers: python_full_version == '3.11.*' and sys_platform == 'linux')
  cause: Because coverage was not found in the cache and rc-metastudio:dev depends on coverage>=7.16.2, we can conclude that rc-metastudio:dev's requirements are unsatisfiable.
```

The ordinary online lock succeeded without changing package versions. The new
psutil declaration promotes the existing pinned transitive dependency to a direct
development dependency. The cache proof's intentionally invalid forms root fails
with exit 1; its full error and exact command remain in the SHA-bound DX-RESUME
log and failed desktop manifest. Earlier failures are retained in TEST-RUNS and
EARLIER-FULL-FAILURES rather than hidden by the later passing runs.

The unmodified text exports intentionally retain trailing empty TSV cells and
public R table-print alignment. The benchmark SVG retains its exact input bytes.
Ordinary `git diff --cached --check` flags that artifact whitespace (exit 2);
`git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check` passes.
Source-code whitespace checks passed before adding these verbatim artifacts.

## Opus review 1 — in progress

All review attempts use `source docs/ux-audit/2026-10-14-round3/ENV.sh`, followed
by `uv run python docs/ux-audit/2026-10-14-round3/run.py LABEL COMMAND...`.
The runner retains exact arguments, exit statuses, transcript hashes and runtime
selection under `raw/`; the final attempt index will preserve earlier records.

Before repair: native precision exited 1 with
`AssertionError: ('non-round ratio tick', '0.135')`; diagnostic exited 1 because
the current-study-order note followed Specificity. HR exited 1 on the repeated
omission-only statement. The expanded collapsed-axis drive first exited 1 with
`AssertionError: ('fp_style', 'Fp Style')` (harness needed the actual style combo),
then exited 1 with `AssertionError: {'1.00'}`. Missing overall flag reproduction
exited 1 because the requested boundary error was absent. Successful source
install `review1-install-reports` exited 0; native HR `review1-reports-hr` exited 0.
Expanded references initially exited 1 with
`ValueError: zip() argument 2 is longer than argument 1` because diagnostic
heterogeneity titles carry a metric prefix. Final exact commands and verbatim
failure blocks will be appended after final verification. One shell edit attempt
also failed with `/bin/bash: line 1: python: command not found`; rerun using
`uv run python` succeeded.

## Opus review 1 — complete command ledger

All commands below ran from the repository root after sourcing `ENV.sh`.
Each was wrapped with `uv run python docs/ux-audit/2026-10-14-round3/run.py LABEL COMMAND`.
`TEST-RUNS.json` retains exact argv/environment/timestamps/revision/log SHA-256,
including the original round failures. Raw logs and child manifests remain
available locally; no nonzero attempt counts as a pass.

| Label | Exit | Exact command |
| --- | ---: | --- |
| review1-before-precision | 1 | `uv run python scripts/verify_rcms.py audit-round3-precision --native` |
| review1-before-diagnostic | 1 | `uv run python scripts/verify_rcms.py audit-round3-diagnostic` |
| review1-before-hr | 1 | `uv run python scripts/verify_rcms.py audit-round3-hr` |
| review1-before-degenerate | 1 | `uv run python scripts/verify_rcms.py audit-round3-precision` |
| review1-before-degenerate-range | 1 | `uv run python scripts/verify_rcms.py audit-round3-precision` |
| review1-install-reports | 0 | `uv run python docs/ux-audit/2026-10-14-round3/install_source.py` |
| review1-before-overall-flag | 1 | `/home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/Rscript -e 'library(RCMetaR); error <- tryCatch({RCMetaR:::rcmetar.forest.regeneration.state("leave-one-out", results=list(list(b=0)), labels="A", has.overall=NULL); NULL}, error=conditionMessage); stopifnot(identical(error, "Sequential forest has.overall must be a single TRUE or FALSE."))'` |
| review1-reports-hr | 0 | `uv run python scripts/verify_rcms.py audit-round3-hr --native` |
| review1-reports-references | 1 | `uv run python scripts/verify_rcms.py audit-round3-references` |
| review1-install-axes | 0 | `uv run python docs/ux-audit/2026-10-14-round3/install_source.py` |
| review1-native-precision-menu-failure | 1 | `uv run python scripts/verify_rcms.py audit-round3-precision --native` |
| review1-golden-drift | 1 | `uv run python scripts/verify_golden_compatibility.py --output-root build/qt6-verification/golden-review1-drift` |
| review1-references | 0 | `uv run python scripts/verify_rcms.py audit-round3-references` |
| review1-golden-drift-valid | 1 | `uv run python scripts/verify_golden_compatibility.py --output-root build/qt6-verification/golden-compatibility-review1-drift` |
| review1-r-presentation | 0 | `/home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/Rscript -e 'testthat::test_local("r/RCMetaR", filter="summary-display\|forest-metafor-renderer", reporter="summary", stop_on_failure=TRUE)'` |
| review1-native-precision-final | 1 | `uv run python scripts/verify_rcms.py audit-round3-precision --native` |
| review1-native-precision-wide | 1 | `uv run python scripts/verify_rcms.py audit-round3-precision --native` |
| review1-golden-parser | 1 | `uv run python scripts/verify_golden_compatibility.py --output-root build/qt6-verification/golden-compatibility-review1-parser` |
| review1-native-precision-passed | 1 | `uv run python scripts/verify_rcms.py audit-round3-precision --native` |
| review1-golden-parser-tests | 0 | `uv run python -m pytest tests/analysis_regression/golden/test_analysis_regression_compare.py -q` |
| review1-numerical-equivalence | 0 | `uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-review1-parser` |
| review1-golden-reviewed-text | 1 | `uv run python scripts/verify_golden_compatibility.py --output-root build/qt6-verification/golden-compatibility-review1-text` |
| review1-native-precision | 1 | `uv run python scripts/verify_rcms.py audit-round3-precision --native` |
| review1-native-precision-complete | 1 | `uv run python scripts/verify_rcms.py audit-round3-precision --native` |
| review1-golden-refresh | 0 | `uv run python scripts/regenerate_golden_presentation.py build/qt6-verification/golden-compatibility-review1-text` |
| review1-native-precision-input | 1 | `uv run python scripts/verify_rcms.py audit-round3-precision --native` |
| review1-golden-strict | 0 | `uv run python scripts/verify_golden_compatibility.py --output-root build/qt6-verification/golden-compatibility-review1-strict` |
| review1-native-precision-included | 0 | `uv run python scripts/verify_rcms.py audit-round3-precision --native` |
| review1-references-final | 0 | `uv run python scripts/verify_rcms.py audit-round3-references` |
| review1-native-hr | 1 | `uv run python scripts/verify_rcms.py audit-round3-hr --native` |
| review1-numerical-strict | 0 | `uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-review1-strict` |
| review1-native-final-hr | 0 | `uv run python scripts/verify_rcms.py audit-round3-hr --native` |
| review1-native-final-irr | 0 | `uv run python scripts/verify_rcms.py audit-round3-irr --native` |
| review1-native-final-diagnostic | 0 | `uv run python scripts/verify_rcms.py audit-round3-diagnostic --native` |
| review1-install-final | 0 | `uv run python docs/ux-audit/2026-10-14-round3/install_source.py` |
| review1-full-final | 130 | `uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh` |
| review1-before-degenerate-labels | 1 | `uv run python scripts/verify_rcms.py audit-round3-precision --native` |
| review1-install-readable-range | 0 | `uv run python docs/ux-audit/2026-10-14-round3/install_source.py` |
| review1-native-readable-precision | 0 | `uv run python scripts/verify_rcms.py audit-round3-precision --native` |
| review1-native-readable-hr | 0 | `uv run python scripts/verify_rcms.py audit-round3-hr --native` |
| review1-native-readable-irr | 0 | `uv run python scripts/verify_rcms.py audit-round3-irr --native` |
| review1-native-readable-diagnostic | 0 | `uv run python scripts/verify_rcms.py audit-round3-diagnostic --native` |
| review1-full-readable | 0 | `uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh` |
| review1-numerical-final | 0 | `uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-r-stack-v2` |
| review1-artifact-whitespace | 2 | `git diff --check cccab01..d6b0b33` |
| review1-source-whitespace | 0 | `git diff --check cccab01..d6b0b33 -- . ':(exclude)docs/ux-audit/2026-10-14-round3/screenshots/review1/*.txt'` |

### Verbatim nonzero attempt diagnostics

Deliberate before-repair failures, presentation drift, fixture mistakes and
the stopped first full run are retained below. Repeated identical diagnostics
within one helper transcript are printed once. Full assertion payloads are
retained when the exception contains the report. Golden comparison rows are
copied directly from the printed JSON; no numerical oracle was refreshed.

`review1-before-precision` — exit 1

```text
AssertionError: ('non-round ratio tick', '0.135')
```

`review1-before-diagnostic` — exit 1

```text
AssertionError: Project: typed.rcms
Confidence level: 95.0%

Sensitivity
Model: Diagnostic Random-Effects
Estimator: DerSimonian-Laird
Inference: Normal approximation

Specificity
Model: Diagnostic Random-Effects
Estimator: DerSimonian-Laird
Inference: Normal approximation
Order: current study order; each row adds a study to the preceding studies.
```

`review1-before-hr` — exit 1

```text
AssertionError: Leave-one-out meta-analysis — Mortality · Time-to-event · Hazard Ratio
Comparison: Locoregional treatment plus chemotherapy / Locoregional treatment alone · Follow-up: first

Model configuration
Project: Pignon2000-HR.rcms
Model: Random-effects inverse variance
Estimator: DerSimonian-Laird
Inference: Normal approximation
Confidence level: 95.0%
Omission-only fits: each row omits the named study. No all-studies fit is included.
HR = 1 means equal hazards in Locoregional treatment plus chemotherapy and Locoregional treatment alone; estimates are fitted on the log scale.

Sequential Summary

Model Results
Study omitted	Estimate	Lower bound (95% CI)	Upper bound (95% CI)	Std. error	p-value
Study omitted: Pitie-74	0.866147	0.806257	0.930485	0.036558	0.000085
Study omitted: Int 0034	0.864739	0.803945	0.930130	0.037193	0.000093
Study omitted: JHCFUS	0.870655	0.811251	0.934409	0.036056	0.000122
Study omitted: TMH R-4	0.865194	0.805665	0.929122	0.036371	0.000069
Study omitted: KKD-86	0.863835	0.804506	0.927540	0.036304	0.000055
Study omitted: HNU-87a	0.865910	0.806335	0.929886	0.036369	0.000075
Study omitted: HNU-87b	0.866035	0.805817	0.930754	0.036771	0.000092
Study omitted: IGR-65	0.865397	0.805782	0.929423	0.036417	0.000072
Study omitted: RTOG 6801	0.862256	0.801623	0.927476	0.037202	0.000068
Study omitted: EORTC 24771	0.862753	0.803091	0.926848	0.036562	0.000054
Study omitted: DENVER-77	0.867484	0.807580	0.931832	0.036508	0.000099
Study omitted: HNCP	0.863086	0.802800	0.927899	0.036944	0.000067
Study omitted: EORTC 78-OCP	0.869331	0.809164	0.933972	0.036594	0.000130
Study omitted: MCW-1	0.860637	0.802140	0.923401	0.035914	0.000029
Study omitted: SWOG 8006	0.862365	0.802641	0.926533	0.036619	0.000053
Study omitted: Pitie-81	0.865256	0.805187	0.929807	0.036711	0.000081
Study omitted: Buenos Aires	0.865989	0.806021	0.930418	0.036614	0.000085
Study omitted: Creteil-82	0.860157	0.801750	0.922820	0.035878	0.000027
Study omitted: HNCGICO2	0.862627	0.803135	0.926527	0.036460	0.000051
Study omitted: MCW-2	0.864286	0.804827	0.928138	0.036366	0.000061
Study omitted: AC CAMARGO (a)	0.864687	0.805040	0.928753	0.036468	0.000067
Study omitted: SECOG II (a)	0.865631	0.805388	0.930379	0.036804	0.000088
Study omitted: EORTC 24844	0.865099	0.805343	0.929288	0.036518	0.000072
Study omitted: SHNG 85	0.863503	0.802795	0.928802	0.037193	0.000080
Study omitted: HNCGICO3	0.863386	0.803769	0.927425	0.036506	0.000057
Study omitted: Creteil-86	0.868351	0.808305	0.932858	0.036560	0.000113
Study omitted: GSTTC-86	0.866986	0.806468	0.932045	0.036918	0.000111
Study omitted: GETTECneo1	0.868937	0.808828	0.933513	0.036574	0.000122
Study omitted: GETTECneo2	0.869736	0.809897	0.933995	0.036369	0.000124
Study omitted: AHNTG	0.865760	0.805300	0.930760	0.036936	0.000095
Study omitted: Las Palmas	0.869884	0.810572	0.933536	0.036031	0.000109
Study omitted: Rennes-87	0.865809	0.805689	0.930415	0.036718	0.000087
Study omitted: Parma	0.861340	0.803104	0.923799	0.035717	0.000029
Study omitted: CFHNS	0.866863	0.806358	0.931909	0.036916	0.000109
Study omitted: Cologne	0.866536	0.806853	0.930633	0.036410	0.000083
Study omitted: Songkla	0.864772	0.805213	0.928737	0.036408	0.000066
Study omitted: HNAP-02	0.862093	0.803953	0.924437	0.035624	0.000031
Study omitted: BNH 003	0.870136	0.810329	0.934356	0.036332	0.000129
Study omitted: MDA-70	0.863885	0.804580	0.927562	0.036286	0.000055
Study omitted: WIA-OC5a	0.869354	0.809742	0.933355	0.036243	0.000112
Study omitted: WIA-OC5b	0.881536	0.825746	0.941095	0.033357	0.000157
Study omitted: EORTC 73-OC	0.862930	0.803000	0.927333	0.036725	0.000060
Study omitted: Bergen	0.868521	0.808894	0.932542	0.036288	0.000102
Study omitted: RT-BLM-73	0.863849	0.804738	0.927301	0.036164	0.000052
Study omitted: WIA-OC5c	0.869810	0.810345	0.933640	0.036131	0.000113
Study omitted: Turku	0.866899	0.807102	0.931126	0.036466	0.000090
Study omitted: UW-77	0.876840	0.819272	0.938453	0.034648	0.000149
Study omitted: NRH-78	0.861462	0.801888	0.925462	0.036563	0.000045
Study omitted: Barcelona	0.867792	0.806607	0.933619	0.037305	0.000144
Study omitted: UW-79	0.873568	0.815672	0.935574	0.034987	0.000112
Study omitted: Manchester	0.863616	0.803174	0.928606	0.037019	0.000075
Study omitted: Yale 80	0.862970	0.803333	0.927033	0.036536	0.000055
Study omitted: PMHCGS	0.865444	0.805087	0.930326	0.036884	0.000089
Study omitted: ECOG 2382	0.861125	0.801340	0.925369	0.036712	0.000046
Study omitted: AC CAMARGO (b)	0.863415	0.804050	0.927163	0.036344	0.000053
Study omitted: Toulouse	0.875800	0.817287	0.938503	0.035280	0.000171
Study omitted: SECOG II (b)	0.868735	0.808493	0.933466	0.036667	0.000124
Study omitted: CH-7401	0.866888	0.807053	0.931159	0.036491	0.000091
Study omitted: Yale 86	0.865604	0.805823	0.929820	0.036513	0.000077
Study omitted: INRC HN-8	0.872707	0.813019	0.936777	0.036146	0.000165
Study omitted: Ontario	0.866929	0.806708	0.931646	0.036733	0.000101
Study omitted: Kragujevac	0.873934	0.814684	0.937494	0.035819	0.000169
Study omitted: Bavaria 89	0.874561	0.815298	0.938132	0.035801	0.000181
Study omitted: LOHNG 91	0.869436	0.809677	0.933605	0.036332	0.000118

leave-one-out

Omission-only fits: each row omits the named study. No all-studies fit is included.

Inference Method

Normal approximation
```

`review1-before-degenerate` — exit 1

```text
AssertionError: ('fp_style', 'Fp Style')
```

`review1-before-degenerate-range` — exit 1

```text
AssertionError: {'1.00'}
```

`review1-before-overall-flag` — exit 1

```text
Error: identical(error, "Sequential forest has.overall must be a single TRUE or FALSE.") is not TRUE
Execution halted
```

`review1-reports-references` — exit 1

```text
ValueError: zip() argument 2 is longer than argument 1
```

`review1-native-precision-menu-failure` — exit 1

```text
AssertionError: ('analysis-data-onearm-proportion', 'meta-regression')
```

`review1-golden-drift` — exit 1

```text
Golden compatibility verification failed: Golden output must use a dedicated golden-compatibility directory
```

`review1-golden-drift-valid` — exit 1

```text
      {
        "classification": "missing_output",
        "dataset": "amino.rcms",
        "detail": "Summary.heterogeneity_df is missing.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      }

      {
        "classification": "numeric_drift",
        "dataset": "amino.rcms",
        "detail": "Summary.q drifted by 15.36 with tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      }

      {
        "classification": "numeric_drift",
        "dataset": "amino.rcms",
        "detail": "Summary.tau_squared drifted by 32.982 with tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      }

      {
        "classification": "text_artifact_drift",
        "dataset": "amino.rcms",
        "detail": "Text section Summary changed.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      }

      {
        "classification": "missing_output",
        "dataset": "continuous.rcms",
        "detail": "Summary.heterogeneity_df is missing.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      }

      {
        "classification": "numeric_drift",
        "dataset": "continuous.rcms",
        "detail": "Summary.q drifted by 6.914 with tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      }

      {
        "classification": "numeric_drift",
        "dataset": "continuous.rcms",
        "detail": "Summary.tau_squared drifted by 11.876999999999999 with tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      }

      {
        "classification": "text_artifact_drift",
        "dataset": "continuous.rcms",
        "detail": "Text section Summary changed.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      }

      {
        "classification": "missing_output",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.heterogeneity_df is missing.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      }

      {
        "classification": "numeric_drift",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.q drifted by 26.259 with tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      }

      {
        "classification": "numeric_drift",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.tau_squared drifted by 41.555 with tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      }

      {
        "classification": "text_artifact_drift",
        "dataset": "lymph.rcms",
        "detail": "Text section Odds Ratio Summary changed.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      }
```

`review1-native-precision-final` — exit 1

```text
AssertionError: [(0.25, 169.89), (0.5, 39.74)]
```

`review1-native-precision-wide` — exit 1

```text
ValueError: zip() argument 2 is shorter than argument 1
```

`review1-golden-parser` — exit 1

```text
      {
        "classification": "text_artifact_drift",
        "dataset": "amino.rcms",
        "detail": "Text section Summary changed.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      }

      {
        "classification": "text_artifact_drift",
        "dataset": "continuous.rcms",
        "detail": "Text section Summary changed.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      }

      {
        "classification": "text_artifact_drift",
        "dataset": "lymph.rcms",
        "detail": "Text section Odds Ratio Summary changed.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      }

      {
        "classification": "unexpected_output",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity_df is an unexpected numeric metric.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      }

      {
        "classification": "unexpected_output",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity_p_value is an unexpected numeric metric.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      }

      {
        "classification": "unexpected_output",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.i_squared is an unexpected numeric metric.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      }

      {
        "classification": "unexpected_output",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.q is an unexpected numeric metric.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      }

      {
        "classification": "unexpected_output",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.tau_squared is an unexpected numeric metric.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      }

      {
        "classification": "unexpected_output",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.heterogeneity_df is an unexpected numeric metric.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      }

      {
        "classification": "unexpected_output",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.heterogeneity_p_value is an unexpected numeric metric.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      }

      {
        "classification": "unexpected_output",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.i_squared is an unexpected numeric metric.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      }

      {
        "classification": "unexpected_output",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.q is an unexpected numeric metric.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      }

      {
        "classification": "unexpected_output",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.tau_squared is an unexpected numeric metric.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      }
```

`review1-native-precision-passed` — exit 1

```text
UNEXPECTED DIALOG: Number of events cannot be greater than number of samples.

AssertionError
```

`review1-golden-reviewed-text` — exit 1

```text
      {
        "classification": "text_artifact_drift",
        "dataset": "amino.rcms",
        "detail": "Text section Summary changed.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      }

      {
        "classification": "text_artifact_drift",
        "dataset": "continuous.rcms",
        "detail": "Text section Summary changed.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      }

      {
        "classification": "text_artifact_drift",
        "dataset": "lymph.rcms",
        "detail": "Text section Odds Ratio Summary changed.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      }
```

`review1-native-precision` — exit 1

```text
  Processing terminated since k = 0.

AssertionError: (<class 'rc_metastudio.results_window.ResultsWindow'>, [])
```

`review1-native-precision-complete` — exit 1

```text
  Processing terminated since k = 0.

AssertionError: (<class 'rc_metastudio.results_window.ResultsWindow'>, [])
```

`review1-native-precision-input` — exit 1

```text
  Processing terminated since k = 0.

AssertionError: (<class 'rc_metastudio.results_window.ResultsWindow'>, [])
```

`review1-native-hr` — exit 1

```text
UNEXPECTED DIALOG: You've made unsaved changes to your data. Do you want to save your changes?

AssertionError
```

`review1-full-final` — exit 130

```text
KeyboardInterrupt
```

`review1-before-degenerate-labels` — exit 1

```text
AssertionError: ('duplicate collapsed-axis labels', 'default', ['0.99', '0.99', '1.00', '1.00', '1.01'])
```

`review1-artifact-whitespace` — exit 2

```text
docs/ux-audit/2026-10-14-round3/screenshots/review1/diagnostic-11-report.txt:23: trailing whitespace.

docs/ux-audit/2026-10-14-round3/screenshots/review1/diagnostic-11-report.txt:38: trailing whitespace.

docs/ux-audit/2026-10-14-round3/screenshots/review1/hr-12-report.txt:53: trailing whitespace.

docs/ux-audit/2026-10-14-round3/screenshots/review1/hr-12-report.txt:54: trailing whitespace.

docs/ux-audit/2026-10-14-round3/screenshots/review1/hr-12-report.txt:55: trailing whitespace.

docs/ux-audit/2026-10-14-round3/screenshots/review1/hr-25-report.txt:44: trailing whitespace.

docs/ux-audit/2026-10-14-round3/screenshots/review1/hr-25-report.txt:45: trailing whitespace.

docs/ux-audit/2026-10-14-round3/screenshots/review1/hr-25-report.txt:46: trailing whitespace.

docs/ux-audit/2026-10-14-round3/screenshots/review1/irr-12-report.txt:53: trailing whitespace.

docs/ux-audit/2026-10-14-round3/screenshots/review1/irr-12-report.txt:54: trailing whitespace.

docs/ux-audit/2026-10-14-round3/screenshots/review1/irr-12-report.txt:55: trailing whitespace.

docs/ux-audit/2026-10-14-round3/screenshots/review1/irr-15-report.txt:15: trailing whitespace.

docs/ux-audit/2026-10-14-round3/screenshots/review1/irr-29-report.txt:44: trailing whitespace.

docs/ux-audit/2026-10-14-round3/screenshots/review1/irr-29-report.txt:45: trailing whitespace.

docs/ux-audit/2026-10-14-round3/screenshots/review1/irr-29-report.txt:46: trailing whitespace.

docs/ux-audit/2026-10-14-round3/screenshots/review1/references-07-report.txt:59: new blank line at EOF.

docs/ux-audit/2026-10-14-round3/screenshots/review1/references-105-report.txt:17: trailing whitespace.

docs/ux-audit/2026-10-14-round3/screenshots/review1/references-14-report.txt:59: new blank line at EOF.

docs/ux-audit/2026-10-14-round3/screenshots/review1/references-22-report.txt:34: new blank line at EOF.

docs/ux-audit/2026-10-14-round3/screenshots/review1/references-30-report.txt:36: new blank line at EOF.

docs/ux-audit/2026-10-14-round3/screenshots/review1/references-45-report.txt:16: trailing whitespace.

docs/ux-audit/2026-10-14-round3/screenshots/review1/references-74-report.txt:16: trailing whitespace.
```

### Final repair results

`review1-full-readable` completed at `c335356` with `--full --fresh`, exit 0.
Its 98 desktop cases ran once with three bounded offscreen workers, with reuse
disabled; all 99 scenario/doctor manifests are bound in REVIEW1-FULL-PROFILE.json.
Observed terminal results:

```text
Status: OK
[RCMetaR-r-stack] Reitsma visual release evidence verified: 21 cases, deterministic hashes and normalized PDF/descriptor contracts
============================== 9 passed in 53.66s ==============================
======================== 98 passed in 982.36s (0:16:22) ========================
```

Both script-generated and saved-bundle Reitsma visual lanes ran 21 cases. Strict
golden comparison passed (474 comparisons, the unchanged 415-field contract),
all 91 independent authority cases passed, and doctor exited 0. Final exact
comparison `review1-numerical-final` exited 0:

```text
415 original fields exactly unchanged; maximum difference 0; original numerical contracts, tolerances, and exceptions unchanged.
```

Native precision, HR, IRR and diagnostic `review1-native-readable-*` all exited
0; each retains inputs, actions, reports, real SVGs, copy/export checks and runtime
provenance in REVIEW1-OBSERVATIONS.json. The references drive also passed fixed
IV standard/sequential/subgroup paths across binary/continuous/diagnostic, MH/Peto
standard paths, and fixed binary/continuous regression. Diagnostic regression has
no fixed path: its joint Reitsma producer retains the actual Reitsma references.
The full profile freshly re-exercised that complete references drive.

All 12 final curated images were inspected individually, including OR/PLO axes,
fixed HR/IRR report/reference tables, IRR omission reporting, diagnostic cumulative
configuration, and all three collapsed forest styles. Screenshot bytes match the
native captures; persistent installed-source inputs and installed package files
match final RCMetaR. INSTALLED-SOURCE.json records the test-owned source install.
Qualified dependency/runtime bytes were not changed.

The stopped first full attempt exited 130 after 98 seconds. The SIGINT targeted
only the recorded launched child tree; REVIEW1-INTERRUPTION.json retains those
commands/PIDs and the reason. No owned child survived. Its attempt remains in the
ledger above and does not count as qualification. The original and earlier review
failures remain in TEST-RUNS.json; one accidentally reused recorder label was
recovered byte-for-byte from the retained child transcripts, verified against its
original SHA-256, as `review1-native-precision-menu-failure`.

The repaired scope is source verification on Linux with native xcb driving.
Release/package qualification and the separate complete low-effort UX re-audit
remain outside this implementation review task. No PR or history rewrite occurred.

`review1-artifact-whitespace` exited 2: Git flags the verbatim exported reports'
trailing tabs (empty final table cells), R's padded printed tables and original
terminal blank lines. These are captured evidence bytes and remain unchanged.
The exact diagnostics are retained in the ledger above. The same check excluding
only those captured TXT payloads (`review1-source-whitespace`) exited 0. This is
not a numerical or desktop failure; stripping the snapshots would discard the
empty cells which R2-03 explicitly requires. No executable source changed.
