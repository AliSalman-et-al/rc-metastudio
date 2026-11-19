# Trial Sequential Analysis phase 3b verification

## Runtime and replay

The paired baselines used Windows x64, native Qt 6.12.0 (`windows`), Python
3.14.10, R 4.6.2 from the RC MetaStudio 0.5.6 distribution, metafor 5.2-1
and gsDesign 3.11.0 where required. The locked Python dependencies and R
dependency binaries were shared across runs. Each baseline installed RCMetaR
from its checked-out source into a separate test-owned library. The fix
(`fc9e8d3447f863e848b24f4d8029021b9e256345`) leaves the RCMetaR source tree
unchanged from `5f073c8f`, so the fixed run uses the branch's installed library.
Each desktop manifest and runtime record identifies the observed checkout, R
library, Qt build and platform. Poppler 26.09.0 decoded the report PDFs.

[replay.ps1](replay.ps1) records the exact invocations, exits, environment
and strict Ty transcript under the named run. It first runs `uv sync --locked`,
generates Qt forms with
`uv run python scripts/build_qt6.py generate --build-root build/qt6-verification`
and runs the repository-wide strict Ty gate targeting `win32`. Native pytest
uses `QT_QPA_PLATFORM=windows`. The paired default-DPI commands leave
`QT_SCALE_FACTOR` unset. The supplemental native commands use
`QT_SCALE_FACTOR=0.8` on the 125% Windows display, reproducing the Results
geometry of phase 3.

From the original repository root with the runtime paths in the script in place:

```powershell
git worktree add --detach ../rc-metastudio-tsa-phase3b-master 84d37e15
# While the main checkout is at 5f073c8f:
& ./artifacts/verification/tsa-phase3b/replay.ps1 -Checkout ../rc-metastudio-tsa-phase3b-master -Label master -Full
& ./artifacts/verification/tsa-phase3b/replay.ps1 -Checkout . -Label branch -Full
& ./artifacts/verification/tsa-phase3b/replay.ps1 -Checkout ../rc-metastudio-tsa-phase3b-master -Label master-prefix -LibraryLabel master -ReuseR -PythonOnly -BinaryPrefix -Scale 0.8
& ./artifacts/verification/tsa-phase3b/replay.ps1 -Checkout . -Label branch-prefix -LibraryLabel branch -ReuseR -PythonOnly -BinaryPrefix -Scale 0.8
git worktree add --detach ../rc-metastudio-tsa-phase3b-bisect 8b6b68c1
& ./artifacts/verification/tsa-phase3b/replay-open.ps1 -Checkout ../rc-metastudio-tsa-phase3b-bisect
# With the fixed revision checked out:
& ./artifacts/verification/tsa-phase3b/replay.ps1 -Checkout . -Label fixed -LibraryLabel branch -ReuseR -Tsa -Scale 0.8
```

The first master focused pytest attempt lacked the fresh worktree's `.tmp`
parent and failed fixture setup. The script now creates that parent. The
corrected default-DPI results are under `master-focused/`, and the full
master run had the parent in place before pytest started. The retained
`master-offscreen/` run also completed the whole review scenario with the
plugin used in phase 3.

## Findings

- **Results resize assertions.** At scale 0.8 master produced the same values
  as phase 3 for all three assertions (1329 vs 1600, 1600 vs 1716, and
  1422.88875 vs 1728). Automatic plot fitting caps conventional plots at
  intrinsic size and also constrains non-forest plots by available height.
  The assertions require wider layouts than that existing policy gives. TSA's
  separate automatic enlargement applies only to the TSA plot kind.
- **Project switch.** `2d31c8fd` introduced a project settings write for the
  implicit carry-over fit. This changed the durable project after the first
  ordinary meta-analysis, so the unsaved-changes prompt cancelled opening
  Continuous. The parent `8b6b68c1` opened Continuous. Both targeted
  checkouts used the same shortened review scenario and the same offscreen
  plugin, with a checkpoint after the unmodified second Open assertion.
  The native full scenario also passed on master and failed on the original
  branch at that assertion.
- **Dirty-state fix.** The last successful ordinary fit now stays on the
  live sheet, while TSA can still read recorded analysis settings from a
  saved project. Running default TSA or repeating a saved design leaves
  the project clean. Changing a TSA design is a real project edit and uses
  the usual workspace dirty transition. The BCG drive checks that a Peto
  fit carries into the TSA report without dirtying the project. The MD
  drive saves entered settings, opens the saved project and runs them
  again without another edit. The added BCG test failed on the old head
  at the [ordinary-fit dirty assertion](red/plot-workflow-trial-sequential.log). Both source preflight cases passed offscreen with the fix ([BCG](preflight-bcg/plot-workflow-trial-sequential.log), [MD](preflight-md/tsa-md.log)).

## Commands and results

The selected GUI commands below use `uv run python -m pytest`. Each linked
transcript includes the full node selection and `--basetemp` argument.

| Command or selection | Master `84d37e15` | Original branch `5f073c8f` | Fixed branch | Classification |
| --- | --- | --- | --- | --- |
| `uv sync --locked`, generate Qt forms, install RCMetaR from source | [Sync](master/sync.log), [forms](master/forms.log), [R install](master/install-r.log) passed | [Sync](branch/sync.log), [forms](branch/forms.log), [R install](branch/install-r.log) passed | [Sync](fixed/sync.log), [forms](fixed/forms.log) passed. Reused branch RCMetaR. | Setup |
| Repository-wide strict Ty, `win32` | [Pass](master/typing.log) | [Pass](branch/typing.log) | [Pass](fixed/typing.log) | Gate passed before GUI |
| Three Results resize tests, native default scale | [Two SVG pass, raster fails](master-focused/results.log) | [Same](branch/results.log) | See scale 0.8 rerun | Pre-existing |
| Three Results resize tests, native scale 0.8 | [Three fail](master-prefix/results.log) | [Same](branch-prefix/results.log) | [Same](fixed/results.log) | Pre-existing, geometry-dependent |
| Binary transactional layout module, native | [13 pass, popup visibility fails](master-focused/binary-layout.log) | [Same](branch/binary-layout.log) | [Same](fixed/binary-layout.log), [all 14 offscreen pass](fixed-offscreen-layout/binary-layout.log) | Pre-existing popup assertion |
| `uv run python scripts/verify_rcms.py review-workflows --native` | [Pass](master/review-workflows.log) | [Second Open cancelled](branch/review-workflows.log) | [Pass](fixed/review-workflows.log) | TSA branch regression, first bad commit `2d31c8fd` |
| `uv run python scripts/verify_rcms.py review-workflows`, stopped just after second Open | [Parent `8b6b68c1` passes](8b6b68c1/review-workflows.log) | [`2d31c8fd` first fails](2d31c8fd/review-workflows.log) | Full scenario rerun | Targeted checkout, [temporary test diff](8b6b68c1/review-open.patch) |
| Full native Python, `uv run python -m pytest tests/python -q --basetemp .tmp/tsa-phase3b-python` | [864 pass, 5 fail, 2 skip](master/python.log). Popup visibility assertion fails. | [Access violation in binary `showPopup()`](branch/python.log), exit `0xC0000005`. | Targeted module and repeat sequence below | See crash comparison below |
| Native five-module GUI prefix, scale 0.8 | [94 pass, 1 fail](master-prefix/binary-prefix.log) | [Same](branch-prefix/binary-prefix.log) | Focused binary module rerun above | Same popup visibility assertion |
| Native fast tests and five-module GUI prefix, default scale, excluding `test_code_health.py` | [557 pass, 1 fail, 1 skip](master-crash-prefix/binary-prefix.log) | [Same](branch-crash-prefix/binary-prefix.log) | Focused binary module rerun above | Same popup visibility assertion |
| Three Results resize tests, offscreen | — | — | [All three pass](fixed-offscreen-layout/results.log) | Existing assertions depend on viewport geometry |
| TSA R tests, `Rscript.exe --vanilla -e '<pkgload and testthat>'` | TSA absent | Phase 3 pass | [Pass](fixed/tsa-r.log) | Statistical code unchanged |
| `uv run python scripts/verify_rcms.py tsa-smd --native` | TSA absent | Phase 3 pass | [Pass](fixed/tsa-smd.log) | Ineligible SMD workflow |
| `uv run python scripts/verify_rcms.py tsa-hr --native` | TSA absent | Phase 3 pass | [Pass](fixed/tsa-hr.log) | HR design, plot and quantity exports |
| `uv run python scripts/verify_rcms.py tsa-rr-mh --native` | TSA absent | Phase 3 pass | [Pass](fixed/tsa-rr-mh.log) | Fixed MH RR futility |
| `uv run python scripts/verify_rcms.py tsa-md --native` | TSA absent | Phase 3 pass | [Pass](fixed/tsa-md.log) | MD design save, reopen and repeat |
| `uv run python scripts/verify_rcms.py plot-workflow-trial-sequential --native` | TSA absent | Phase 3 pass | [Pass](fixed/plot-workflow-trial-sequential.log) | BCG plot/report, Peto carry-over and unchanged default design |




### Access violation and remaining red tests

Both full native Python runs used the same command. Master continued past the
binary popup and reported a visibility assertion. The original branch crashed
at that popup, as in phase 3. Both revisions completed the shorter prefixes
with the same visibility failure and no crash.

Keeping full collection but excluding the slow code-health tests and stopping
at the first failure reproduced the Windows access violation on master twice,
at [default scale](master-repeat/python-first-failure.log) and at
[scale 0.8](master-repeat-scale08/python-first-failure.log). Both were in the
native `QComboBox.showPopup()` call for the subgroup selector, earlier in the
suite than the binary selector. The matching [branch repeat](branch-repeat/python-first-failure.log)
stalled at that subgroup test and was stopped after more than three minutes
without progress. Use `replay.ps1 -ReviewOnly -PythonOnly -FirstFailure` for
this repeat and `-Scale 0.8` for its scale variant. The smaller fast-plus-GUI
prefix is selected with `-PythonOnly -BinaryPrefix -FastBeforeBinary`.

This establishes pre-existing native popup instability. The exact binary
access violation was observed only on the branch. Its native fault mechanism
and any branch-specific change in frequency remain undetermined. The popup
assertion and the three Results assertions remain red at scale 0.8. The
offscreen reruns passed all 17 focused assertions. No shared Qt layout code was
changed.

### Retained artifacts

The desktop folders contain complete action and result evidence locally,
including the inputs, screenshots, exports, steps, runtime identities and
manifests. [The hash audit](manifest-audit.log) checked every retained file
listed by the desktop manifests after teardown. The source fixtures are also
copied under `inputs/`. The branch contains the replay scripts and text
transcripts. Bulk desktop artifacts remain in this local evidence directory.
