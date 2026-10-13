# Round-two verification results

Run from the repository root in PowerShell after:

```powershell
. ./docs/ux-audit/2026-10-14-round2/ENV.ps1
```

The packaged R runtime and a persistent test-owned library are used; system R
libraries and user projects were not modified. Each linked record contains exact
argv, cwd, timestamps, source revision, relevant environment, exit status and a
SHA-256 digest of its immutable log. The argv below is the command executed inside
the evidence wrapper; the logs preserve subprocess commands too.

## Baseline and final commands

### before-doctor

```powershell
uv run python scripts/verify_rcms.py doctor
```

Pass: packaged runtime and baseline environment.

Exit 0; revision `36283eec`. [Record](before-doctor.json), [log](before-doctor.log).

### before-authorities

```powershell
C:\Users\Ali-Salman\Documents\Code\rc-metastudio\build\windows-package\dist\RCMetaStudio\R/bin/Rscript.exe .agents/skills/verify-rcms/scripts/analysis_authorities.R docs/ux-audit/2026-10-14-round2/before-authorities-results.json
```

Pass: 91 authority cases.

Exit 0; revision `36283eec`. [Record](before-authorities.json), [log](before-authorities.log).

### before-golden-retry

```powershell
uv run python scripts/verify_golden_compatibility.py --output build/qt6-verification/golden-compatibility-round2-before-retry
```

Pass: 11 cases, 474 comparisons after correcting R DLL search path.

Exit 0; revision `3b40e814`. [Record](before-golden-retry.json), [log](before-golden-retry.log).

### before-r-tests

```powershell
uv run python -m pytest tests/r_stack -q -ra
```

Pass: 9 bridge tests.

Exit 0; revision `36283eec`. [Record](before-r-tests.json), [log](before-r-tests.log).

### full-python-final-source

```powershell
uv run python scripts/run_with_timeout.py --timeout-seconds 600 --label round2-python-final-source -- C:\Users\Ali-Salman\Documents\Code\rc-metastudio\.venv\Scripts\python.exe -m pytest tests --ignore=tests/r_stack --ignore=tests/e2e -q -ra -n 2 --dist loadfile --durations=15
```

905 passed, 2 skipped in 214.12 s. Skips: POSIX process-group teardown and native macOS PyInstaller BUNDLE.

Exit 0; revision `a18ba959`. [Record](full-python-final-source.json), [log](full-python-final-source.log).

### typing-final-source

```powershell
uv run ty check --extra-search-path build/qt6-verification/generated/rc_metastudio --extra-search-path build/qt6-verification/generated/rc_metastudio/forms --extra-search-path . --extra-search-path src/rc_metastudio --extra-search-path src --extra-search-path scripts --extra-search-path tests/python/gui src/rc_metastudio scripts tests r/RCMetaR/inst/qa
```

Pass: all type checks passed.

Exit 0; revision `a18ba959`. [Record](typing-final-source.json), [log](typing-final-source.log).

### full-r-stack-final-source

```powershell
uv run python scripts/verify.py r-stack --r-runtime-root C:\Users\Ali-Salman\Documents\Code\rc-metastudio\build\windows-package\dist\RCMetaStudio\R
```

Overall exit 1 at the strict golden gate only. R build/check: 1 NOTE; Reitsma release evidence: 21 cases with deterministic hashes/normalized PDF and descriptor contracts; bridge: 9 passed in 58.04 s; desktop E2E: 85 passed in 777.59 s. Golden capture passed; artifact comparison failed as documented below.

Exit 1; revision `d7b36ee3`. [Record](full-r-stack-final-source.json), [log](full-r-stack-final-source.log).

### package-handoff

```powershell
uv run python docs/ux-audit/2026-10-14-round2/package_check.py
```

Final R source: 1782 assertions passed, 0 failures, 0 warnings, 1 optional visual-QA skip. R CMD check: 0 errors, 0 warnings, 1 NOTE for declared but unused tiff import. The separate 300-case matrix exercises visual QA.

Exit 0; revision `ddd492b0`. [Record](package-handoff.json), [log](package-handoff.log).

### bridge-handoff

```powershell
uv run python -m pytest tests/r_stack -q -ra
```

Final installed R source: 9 passed in 53.94 s; no missing-runtime skips.

Exit 0; revision `7d06a671`. [Record](bridge-handoff.json), [log](bridge-handoff.log).

### authorities-handoff

```powershell
C:\Users\Ali-Salman\Documents\Code\rc-metastudio\build\windows-package\dist\RCMetaStudio\R/bin/Rscript.exe .agents/skills/verify-rcms/scripts/analysis_authorities.R docs/ux-audit/2026-10-14-round2/authorities-handoff-results.json
```

Pass: 91 authority cases; exact baseline case dictionaries unchanged.

Exit 0; revision `ddd492b0`. [Record](authorities-handoff.json), [log](authorities-handoff.log).

### new-output-handoff

```powershell
C:\Users\Ali-Salman\Documents\Code\rc-metastudio\build\windows-package\dist\RCMetaStudio\R/bin/Rscript.exe docs/ux-audit/2026-10-14-round2/output-authorities.R docs/ux-audit/2026-10-14-round2/new-output-handoff-results.json
```

Pass: 84 independent public metafor comparisons, 21 metrics × z/t/knha/adhoc, including PAS boundary stress, PI, overall test, subgroup QM/F/df/P and t/Z table headings.

Exit 0; revision `ddd492b0`. [Record](new-output-handoff.json), [log](new-output-handoff.log).

### golden-handoff

```powershell
uv run python scripts/verify_golden_compatibility.py --output build/qt6-verification/golden-compatibility-round2-handoff
```

Expected exit 1 retained: 11 case captures passed; 474 comparisons = 447 pass + 13 pre-existing accepted exceptions + 14 text/artifact drift. No numerical drift; no oracle/tolerance/exception update.

Exit 1; revision `ddd492b0`. [Record](golden-handoff.json), [log](golden-handoff.log).

The full R-stack lane began at `d7b36ee`; the later Python-only diagnostic
report-order change passed the complete 905-test suite. The final R subgroup t/Z
caption change passed the final package check, 84 independent output comparisons,
91 authorities, 11 golden captures and nine bridge tests. The 85 desktop workflows
were not repeated after that caption-only change; the full-stack result above is
not described as a completely green gate.

## Native and figure evidence

```powershell
./docs/ux-audit/2026-10-14-round2/NATIVE.ps1 -Phase after-final
```

22/22 native scenarios passed. NATIVE.ps1 contains the exact serial scenario list;
RUNS.json expands every command, and NATIVE-INDEX.json identifies every complete
hash-checked input/project/runtime/action/result/export bundle. Later targeted
native runs verify the corrected clinical-first and combined reports, actual factor
contrasts, complete Year/CI cells and calculator values, endpoint caps, subgroup
test table and editor labels. Native Qt scaling at 1.25, 1.5 and 2 passed. Report
selection/full copy, Tables shortcut/copy, table CSV cells and existing figure
exports were exercised. 58 selected screenshots were manually checked for readable
glyphs and layout. Raw original bundles remain under artifacts/verification/rcms;
the curated PNGs are committed here.

Two full 300-case forest matrices have zero renderer errors and all 600 retained
PNGs decode successfully. This is automated image integrity evidence, not manual
review of every matrix raster. Exact rendering commands are in RUNS.json and
FOREST-VALIDATION.json records file hashes/dimensions. Raw matrix PNGs remain local
and are ignored; manifest CSVs and the reviewed native selections are committed.

## Numerical equivalence and retained artifacts

```powershell
uv run python docs/ux-audit/2026-10-14-round2/numerical_equivalence.py
uv run python docs/ux-audit/2026-10-14-round2/validate_artifacts.py
uv run python docs/ux-audit/2026-10-14-round2/collect_evidence.py
uv run python docs/ux-audit/2026-10-14-round2/verify_retained_evidence.py
```

NUMERICAL-EQUIVALENCE.json: all 415 frozen fields across 11 cases are exactly
unchanged (maximum absolute difference 0); all 91 authority case dictionaries are
unchanged. The baseline/oracle directory has no diff. Newly displayed quantities
have separate reference-package evidence; they do not replace frozen oracle fields.

golden-final/ retains the final comparison report, manifest and case captures;
golden-before/ retains the passing baseline report and captures. package-final/
retains 00check.log and testthat.Rout; the tarball and complete check directory
remain in build/verification/round2-package-check. INSTALLED-SOURCE.json binds
installed package, source and check-artifact hashes. SOURCE.json binds relevant
Python/R/helper source. RUNS.json is the exhaustive command ledger, including
failed and superseded runs.

EVIDENCE-INTEGRITY.json proves all 191 raw committed log digests and 58 curated
screenshot digests match their records, all 22 final native scenarios passed,
and the oracle directory is unchanged. Local .gitattributes preserves evidence
bytes across checkout; raw logs are not whitespace-normalized.

## Failures and qualification limits

The first baseline golden attempt failed to load stats.dll: fixed the process-local
R bin/x64 search path, then captured a passing baseline before implementation.
Early probes retained genuine clinical-order, zoom, CSV reset/teardown, report/table
geometry, diagnostic title/dispatch, partial sequential rendering, endpoint-cap,
factor-contrast, grid-width, PAS PI and subgroup-caption failures. Obsolete label
assertions, a golden fixture stub, Windows locale and help-modal capture issues were
also corrected. Failed/terminated attempts remain in the ledger with logs and owned
PID-tree termination evidence. The earlier 80/85 desktop run failed five scenarios;
the corrected full lane passed all 85.

The final strict golden and aggregate R-stack exits remain 1 because intended
presentation changes cause 14 artifact differences. No numeric drift is accepted.
The package's tiff dependency NOTE is retained. NVDA/Narrator, Windows High Contrast,
multi-monitor/OS display scaling, complete keyboard-only traversal and broad light
theme qualification were not performed. Qt scale-factor checks do not establish
those claims. Legacy free-form R printouts and HR/IRR moderator printouts remain
selectable wrapping text rather than fully structured coefficient tables.
