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
