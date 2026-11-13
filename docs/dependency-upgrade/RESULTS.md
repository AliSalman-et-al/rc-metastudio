# Dependency qualification

This change upgrades the supported runtime combination to Python 3.14.10,
R 4.6.2, Qt/PyQt 6.12.0, rpy2 3.6.9 and ty 0.0.102. Python dependencies are
exactly pinned in `pyproject.toml`/`uv.lock`; R binaries use the dated Posit
2026-11-13 snapshot. All 151 binary package versions agree across the three
native target indices. The original frozen numerical archive and its tolerances
remain unchanged.

Ty uses Astral defaults with warnings fatal. Cleanup removes obsolete Qt
suppressions, guards nullable Qt results and specifies real container shapes.
The gate also covers `.agents/skills/verify-rcms/scripts/`; 57 diagnostics in
that previously omitted folder are fixed using existing Qt test helpers and
precise container shapes. The installed workspace `.venv` now uses the upgraded lock; the original
Python environment remains at `build/dependency-baseline-python`.

R installers now include recommended packages in the dated binary closure and
replace target copies whose versions differ. This updates bundled nlme from
3.1-171 to 3.1-172 and development-library mgcv from 1.9-4 to 1.9-5. The final
selected R library has no package behind the snapshot.

## Final local qualification before PR

The fresh complete desktop command passes all **133 cases** in 3,484.84 seconds,
then passes a fresh runtime doctor. This supersedes the earlier composed
qualification below without changing or relabelling any failed attempt. All
application, test and configuration inputs remained frozen at `eb94c2c1` during
this run. Subsequent Windows CI corrections are described below; they do not
change application or statistical behavior.

The controller retains exact commands, timestamps and exit codes in
`artifacts/verification/dependency-upgrade-20261113/local-pr-qualification/results.json`.
Its completed stages and final controls are below. Paths starting with
`local-pr-qualification/` are relative to that evidence root.

| Check | Observed result | Evidence |
| --- | --- | --- |
| Expanded strict typing, win32 target on Linux | Pass, including skill drivers, with warnings fatal | `artifacts/verification/typing/20261113T181519-f27f4db8/` |
| Complete non-desktop Python suite | 1,083 passed, 21 platform skips; all ten real-R bridge tests exercised | `local-pr-qualification/python.log`, `local-pr-qualification/python.xml` |
| Code health | Pass on committed source | `local-pr-qualification/code-health.log` |
| R package build and check | Status OK; 2,228 assertions, four intentional reference-fit warnings, one optional visual skip | `local-pr-qualification/r-build/RCMetaR.Rcheck/` |
| Optional forest visual matrix, run separately | Seven assertions pass, no warnings or skips; all 300 PNGs decoded and hashed | `local-pr-qualification/forest-300.log`, `local-pr-qualification/forest-retained-index.json` |
| Fresh complete desktop matrix and doctor | 133 passed, zero failed; aggregate exit zero | `artifacts/verification/rcms/20261113T131814Z-b50b6d94-complete/summary.json`, `00.log`, `01.log` |
| Independent statistical authorities and installed versions | 103 public-package comparisons pass; runtime and package pins match | `local-pr-qualification/authorities.json`, `local-pr-qualification/manifest-versions.log` |
| Reitsma visual controls | 21 semantic cases pass twice with deterministic hashes | `local-pr-qualification/reitsma.log`, `local-pr-qualification/reitsma-visual-qa-{1,2}/` |
| Fresh frozen numerical comparison | 11 cases, 475 comparisons, 416 numeric fields pass with unchanged oracle and tolerances | `build/qt6-verification/golden-compatibility-local-pr-qualification/capture/compatibility-report.json` |
| Final evidence audit | 130 desktop workflows plus three geometry controls pass; 16,993 desktop artifacts and 300 forest image hashes verified | `local-pr-qualification/qualification-audit.json` |
| Repository pre-push lane | All six stages pass: generation, typing, code health, fast/golden, GUI and packaging contracts | `local-pr-qualification/pre-push.log`, `local-pr-qualification/pre-push.json` |

The Python/R stages completed before a turn interruption. The resumed controller
retained only completed zero-exit stages with unchanged inputs, reran the
interrupted optional forest stage, and ran the desktop matrix fresh. The partial
forest artifacts and interruption record remain under `local-pr-qualification/`.
Two golden-command setup attempts were rejected before capture: first for an
output outside `build/qt6-verification`, then for omitting the required
`golden-compatibility-` directory prefix. Their logs/results remain retained;
the corrected command passes without source or oracle changes. See
`local-pr-qualification/extra-results.json` and its linked prior attempts.

## Windows PR qualification corrections

PR #589's first CI run exposed two upgrade omissions that the Linux platform
skips did not exercise. The public Windows packager and its cache key still
contained R 4.6.1's SHA-256 after their version/URL moved to R 4.6.2. A fresh
download of the official 91,363,600-byte R 4.6.2 installer hashes to
`b0b0053baa1963b6d8a28c9642d50107ef9ce2f41c8b9a90e952846c8918b38a`,
matching the already upgraded integration-kit pin. The Windows packager and
cache key now use that value. Native Authenticode validation remains required.

Two Qt rejection controls had also been changed to the valid new version during
the upgrade, so they no longer created mismatches. Both now use `0.0.0` as an
explicit invalid version. Running the existing full Windows deployment negative
control function with real PE parsing on Linux reproduces the original failure,
then passes after correction. This verifies portable inspector behavior, not
native Windows execution. Strict typing passes; the locally runnable packaging
suite reports 132 passed and 14 platform skips. No GUI or statistical code,
oracle, or tolerance changed.

Evidence lives under
`artifacts/verification/dependency-upgrade-20261113/ci-recovery-589/`:
`package.log`, `contract.log`, `controls-before.log`, `controls-after.log`,
`typing.log`, `packaging-local.log`, `r-installer.headers`, the retained official
installer, and `r-installer-verification.json`. CI must qualify the corrected
Windows package and native contract suite before merge.

## Earlier evidence and recovery history

Unless explicitly rooted elsewhere, evidence paths below live under
`artifacts/verification/dependency-upgrade-20261113/`. Earlier short filenames in
`decisions.tsv` use that same evidence root. Superseded and failed attempts remain
available; they are not passing qualification claims.

| Check | Observed result | Evidence |
| --- | --- | --- |
| Latest typing gate, Windows target on Linux | Pass, Astral defaults and warnings fatal, including all six corrected driver/fixture files | `desktop-irr-bounded.log`; `artifacts/verification/typing/20261113T162628-ec8aa815/` |
| Python fast, Qt GUI, packaging and golden selection | 1073 passed, 21 skipped; 43 affected checks pass again after review corrections | `python-final-qualification.log`, `review-recovery-tests.log` |
| Broad fast suite, then affected recovery | Initial 482 passed, 6 skipped, 3 harness failures; all 100 affected checks passed after correction | `candidate-fast.log`, `fast-failure-recovery.log` |
| R installer/manifest/package policy selection | 40 passed, 4 native-platform skips | `recommended-policy-checks.log` |
| Full test collection with real R | 1237 collected | `full-collection.log` |
| Original Python/R frozen comparison | 11 cases, 475 comparisons, including 416 numerical fields; pass | `baseline/source/build/qt6-verification/golden-compatibility-baseline/compatibility-report.json` |
| Original R authority matrix | 103 cases pass | `baseline/authorities.json`, `baseline/authorities.log` |
| Independent small-study checks, old and new | 11 cases pass on each; no numerical drift; negative controls detect mismatches | `small_study_authorities.R`, `small-study-{baseline,candidate}.json`, `small-study-comparison.json` |
| Final R package/version/index audit | 169 selected packages; 151 binary versions agree across targets; no outdated selected version | `audit_selected_r_versions.py`, `final-r-version-audit.json` |
| Native source workflow, real Qt/R | Amino workflow passes on Linux XCB, Qt 6.12, R 4.6.2, metafor 5.2-1 | `native-amino-final.log`; `artifacts/verification/rcms/20261113T083933Z-bd48eee5-amino/` |
| Native shell/import/menu/status rendering | Pass on Qt 6.12; explicit R boundary double, no statistical claim | `native-qt612.log`, `native-qt612/` |
| Current-source R package, authorities, bridge and Reitsma gates | R CMD check Status OK: 2228 assertions, four understood warnings and one optional visual skip; 103 authority cases, 10 bridge tests and 21 Reitsma cases pass | `final-r-stack-artifacts/`, `candidate-audited-full.log`; `artifacts/verification/rcms/20261113T084309Z-aa628a50-complete/00.log` |
| Candidate frozen comparison | 11 cases, 475 comparisons and 416 numerical fields pass | `build/qt6-verification/golden-compatibility-dependency-upgrade/` |
| Corrected native menu/contrast workflow | Pass on XCB; contrast improves from 3.98:1 to 4.97:1 | `artifacts/verification/rcms/20261113T091917Z-184eda51-review1-design/` |
| Complete 133-case desktop matrix | 129 passed, four driver failures; targeted recovery described below | `desktop-post-review.log`; `artifacts/verification/rcms/20261113T095830Z-e638f11b-complete/` |
| Targeted desktop recovery | All four originally failed scenarios pass; HR and funnel controls pass too; all 133 unique obligations have passing evidence | `desktop-fixture-recovery.log`, `desktop-caption-recovery.log`, `desktop-irr-bounded.log`, `desktop-qualification-audit.json` |
| Corrected metadata fixtures | 22 passed, seven native Windows skips; current Windows runtime identity accepted and old rpy2 rejected | `fixture-focused-tests.log`, `windows-probe-fixture-{before,after}.log` |
| Fresh runtime doctor | Pass on final application/runtime | `final-doctor.log`; `artifacts/verification/rcms/20261113T110420Z-67ac59f0-doctor/` |
| Retained desktop evidence audit | 17,817 artifact hashes verified; recovery Python/R/runtime/environment inputs identical except the bounded driver delta | `audit_desktop_qualification.py`, `desktop-qualification-audit.json`, `desktop-qualification-audit.log` |
| Extracted final Linux package qualification | Pass after review corrections | `linux-package-reviewed.log`, `final-linux-package-evidence.json`; archive SHA-256 `85fa22fb3ed061b17b146614b8337429813bfcabee5901d81c43dcab271c9621` |

The three fast-suite failures were test harness issues: two simulated Windows
locale environments omitted `PROCESSOR_ARCHITECTURE`, and a typing helper copied
a JSON list that its caller needed to mutate. The existing failure tests exposed
these issues before correction. A separate probe also restored original rejection
of an entire malformed plot-descriptor list after narrowing.

The first full profile passed its R/scientific stages, then was interrupted after
two desktop failures. The menu driver checked for a dialog before its scheduled
menu click had run; a bounded event wait fixes it without changing the action.
A nine-refit scenario timed out while making progress at 120 seconds, but passed
in isolation in 64 seconds; it now receives 240 seconds in parallel runs. Native
recovery also exposed insufficient contrast in the existing gold result-cell
tint. Reducing alpha from 110 to 80 raises the observed contrast to 4.97:1. The
rebuilt package passes; the complete desktop matrix ran against final source.
An existing unit fixture still expected alpha 110; it was updated to 80, the
complete 1073-test Python selection passed, and the desktop controller restarted
so all retained scenario signatures refer to that final source.

That earlier matrix completed with 129 passes and four failures. Both manuscript
drivers expected the old `metafor 5.0.1` citation; the application correctly
reports 5.2.1. The XLSX driver treated the intended legacy `.xls` warning as
unexpected. It now checks the exact warning, clicks OK and retains the existing
invalid-workbook and dataset-preservation assertions. The Windows positive
packaging fixture also now uses cp314 and the current three rpy2 distribution
versions; its deliberate old-version negative control still rejects the mismatch.

The fourth failure was an invalid requirement that an entire generated figure
caption fit inside a screen-bounded QLineEdit. The real old Qt 6.11 and new Qt
6.12 editors both have a 638-pixel field and 642-pixel caption, with identical
keyboard access to the complete text. Both also preserve and select a
1,000-character caption. The driver now proves Home/End/full-selection access
and retains the fit assertions for the other heading fields. See
`check_caption_scroll.py`, `caption-scroll-baseline-observed.log` and
`caption-scroll-candidate.log`. The moved baseline environment's compiler
entrypoint shebangs selected the new workspace interpreter, so the old probe
forms were generated through the old compiler API; failed setup attempts remain
retained alongside `generate_baseline_caption_forms.py`.

The first targeted batch passed both manuscript paths, XLSX import and the
funnel workflow. Its HR/IRR cases exposed a driver error introduced by the new
keyboard check: a branch-local import shadowed the existing module helper.
Removing that import repairs the scope; HR passes. Parallel IRR reached 232
steps and isolated IRR reached 193 steps before their 600-second limits, without
an assertion failure. Only IRR now receives a 1,200-second hard verification
bound; its complete workflow passed in 610.46 seconds. See `desktop-caption-recovery.log`,
`desktop-irr-isolated.log` and `desktop-irr-bounded.log`. Host load was observed,
but no matched old-stack timing benchmark was captured; the allowance is not
evidence that the new stack is faster or equally fast.
No application, runtime, statistical fixture or tolerance changed during this
recovery. `fixture-recovery-delta.json` and `fixture-recovery.patch` bind the six
changed test/driver files and prove unrelated driver functions byte-identical.
The original full command remains failed; targeted success does not relabel it
or rewrite its evidence/cache entries. The earlier qualification consisted of its 129 passes,
four successful targeted recoveries, the HR/funnel controls and fresh doctor.
The audit verifies all 17,817 retained artifacts and confirms that the recovery
runtime/environment matches the original matrix. All 133 distinct obligations
had passing evidence at that point. The fresh final command above now passes all
133 cases together.

The four R test warnings come from intentionally incomplete direct reference
fits in `test-statistics-02.R`. The old subset emits the same messages, among 48
warnings; the full new suite emits only those four. That earlier run skipped the
optional 300-image forest matrix, which the final local qualification exercises
separately; the required 21-case Reitsma visual gate
passed twice with deterministic hashes. See `r-warning-comparison.json` and the
retained test transcript. The 99 authority cases with captured values have no
version drift at the report’s retained precision; the other four cases retain
assertion-only success. Runtime comparisons with public package calls retain
their original strict tolerances.

## Reproduction

Use the repository's qualified task-owned R library and generated Qt forms:

```sh
source artifacts/verification/dependency-upgrade-20261113/candidate-env.sh
.venv/bin/python .agents/skills/verify-rcms/scripts/verify_all.py --full
.venv/bin/python scripts/audit_dependency_versions.py \
  --rscript "$R_HOME/bin/Rscript" \
  --output artifacts/verification/dependency-upgrade-20261113/candidate-inventory.json
.venv/bin/python artifacts/verification/dependency-upgrade-20261113/audit_selected_r_versions.py
```

The Linux build used `build/dependency-package-python/bin/python` and
`scripts/build-linux-package.sh`. Its download transport replayed verified retained
upstream binary responses/archives through the task-owned `cached_curl.py`, with
SHA-256 checks and a `package-cache-replay.jsonl` transcript. This avoids flaky
DNS and repeats the actual binary-only installer, private R build, PyInstaller,
archive extraction and native application checks. It does not establish live
network reliability. Exact R installers, binary package archives, indices and
upstream response headers are retained in the evidence roots.

## Matched Amino timing continuation

Five fresh-process runs per stack were alternated old/new after separate
profiling runs. All ten measured runs and both profiling runs passed identical
action sequences and the unchanged numerical contract. The input project and
oracle are byte-identical across the two source trees. All 600 retained artifact
hashes were verified.

| Stack | Median seconds | Range seconds | Measured runs |
| --- | ---: | ---: | ---: |
| Original Python/R/Qt stack | 43.58 | 36.61–55.04 | 5 |
| Upgraded stack | 41.04 | 35.55–45.88 | 5 |

The speed difference is inconclusive: ranges overlap on a busy host. Profiling
attributes most elapsed time to embedded R evaluation, but CPU versus I/O within
R was not separately isolated. The measured region includes startup, two real
fits, numerical assertions and evidence capture; its preceding typing gate is
excluded. This is an automated workflow comparison, not pure click-to-result
latency, a broad speed guarantee, or an IRR performance comparison.

Reproduce with `timing-continuation/measure.py`, then
`timing-continuation/analyze.py` under the evidence root. Exact commands, runtime
identities, load averages, profiles, per-run results and evidence paths are in
`timing-continuation/runs.json`, `summary.json`, `README.md` and `*.pstats`.
The linked Windows machine was still unreachable on recheck; no macOS machine
was linked. The native qualification limits below remain.

## Remaining qualification

The host is Linux Mint 22.3 on the Ubuntu Noble/glibc 2.39 base. Local Linux
source/package checks do not establish the exact Ubuntu 24.04 release target or
native Windows x64 and macOS arm64 qualification. Those target workflows and pins
are updated; no release workflow, signing, publication or promotion was invoked.
Opus 5.5 Medium approved the GUI and found no blocking source issues. Its review
flagged the omitted driver typing scope and stricter ratio display conversion.
The scope is now included and clean; the converter again delegates coercion to
Python float, matching original HEAD across 22 cases including NumPy scalars,
Decimal, Fraction, byte buffers and custom numeric protocols. All 43 affected
workspace/verification/table checks pass. See `typing-expanded-final.log`,
`display-coercion-{before,after}.log` and `review-recovery-tests.log`.

The [independent Opus 5.5 Medium review](t3-thread://v2/82c4de75-dad2-4395-8244-3a9f6832bc69/thread:delegated-task:command%3Amcp%3A84d3352a-e3a0-4162-9389-12061d555d82%3Adelegate-task%3A8f0dd8e8-cbc6-4627-a5fc-3abf9b1302e0)
approved the GUI before the final matrix. Subsequent recovery changes only
test/driver expectations; the GUI design remains approved.

The rebuilt final package passes after that conversion correction; the prior
GUI-approved artifact is retained under `pre-review-package/`. No old-stack
timing comparison was performed for `review-workflows`; its 240-second allowance
is a bounded harness budget, not evidence of a performance improvement.
