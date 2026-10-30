# Sheet migration evidence

Status: baseline preparation only. The sheet-owned runtime, v3 seam and writer,
tabs, undo operations and sample conversion are **not implemented**. No numerical
oracle or bundled project has changed. This increment preserves the working app.

## Reproduce the original corpus capture

Generate forms with `uv run python scripts/build_qt6.py generate --build-root
build/qt6-verification`. Select the pinned R 4.6.1 runtime and a worktree-owned
library containing the current RCMetaR source, then run:

```sh
uv run --no-sync python scripts/sheets_baseline.py build/sheets-baseline/original-corpus-complete
```

Use a new output directory for each invocation. The script refuses to overwrite
one. It retains byte-identical original archives, SHA-256 hashes, declared pairs,
saved settings, current R source hashes, command and runtime environment. It
opens those retained files through the production desktop path and records the
default random-effects analysis's numerical sections for every declared pair.
`numerics.json` is written only after all pairs complete. The standard helper
retains runtime identity, action/configuration/result screenshots and plots.

This is baseline capture, not an independent statistical oracle or a conversion
equality assertion. The existing frozen gates remain authoritative. Additional
HR/IRR fixed, subgroup and MH analyses still require `ratios-samples`; this
recorder alone does not satisfy the complete requested sample proof.

Completed original capture: **8/8 pairs**, exit 0. Numerical sections are in
`build/sheets-baseline/original-corpus-complete/numerics.json`; original inputs
and inventory are beside it. Helper evidence:
`artifacts/verification/rcms/20261030T225528Z-3eb6931f-sheets-baseline`.

| Original file | Version | Pairs → intended sheets | Conversion equality |
| --- | --- | --- | --- |
| BCG.rcms | 1 | 1 → 1 | Not run |
| NielWeise2008-IRR.rcms | 2 | 1 → 1 | Not run |
| Pignon2000-HR.rcms | 2 | 1 → 1 | Not run |
| amino.rcms | 1 | 2 → 2 | Not run |
| continuous.rcms | 1 | 1 → 1 | Not run |
| lymph.rcms | 1 | 1 → 1 | Not run |
| meantime.rcms | 1 | 1 → 1 | Not run |

## Runtime and native evidence

R home: `/home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home`.
The supplied `r-library` cannot load RCMetaR because `farver` is missing. Copied
`r-stack-retained-273bd6a` into this worktree's `build/sheets-r-library` and
installed `r/RCMetaR` there; no shared or system library was changed. Installation
log and source hashes: `build/sheets-baseline/r-install.log` and
`build/sheets-baseline/r-source-installed.json`. Generated forms are local to
`build/qt6-verification`. Exact environment: `build/sheets-baseline/ENV.sh`.

The locked rpy2-rinterface 3.6.6 wheel lacked its required API module. Rebuilt
that version from source with `RPY2_CFFI_MODE=API` and `LIBRARY_PATH` pointing at
the supplied read-only `ux-round3/link-libs`. Retained build log:
`build/sheets-baseline/rpy2-api-install-linked.log`. Use `--no-sync` to retain
the locally compiled bridge.

Doctor passed: `artifacts/verification/rcms/20261030T225131Z-a97e7ad9-doctor`.
Native Aminoglycosides passed the existing frozen numeric contract:
`artifacts/verification/rcms/20261030T225642Z-c0387de3-amino`.
Before captures: [main window](screens/sheets-before-main.png) and
[analysis setup](screens/sheets-before-analysis.png). These are native xcb
captures; there are no after screenshots yet.

The full desktop command was started but interrupted: **1 passed, 0 reported
failures; remaining scenarios unverified**, exit 2. Transcript:
`build/sheets-baseline/e2e-matrix.log`. This is not a green matrix. Initial
startup failures and the first 120-second corpus timeout remain in the evidence
directories; neither is counted as a product regression or silently discarded.

## Remaining acceptance work

Follow DESIGN.md's migration increments and failure table. In particular, write
the new sheet interaction drives before replacing the runtime graph. Prove
independent row ownership, sheet ID based undo after switching, add/rename/delete,
two-swap identity, disabled noncomparative swap, save/reopen, naming collisions
and legacy multi-follow-up conversion. Preserve raw precision and inactive arms.
Then run the frozen numerical/golden gates, full desktop matrix and full skill
profile. Convert samples only after the production v3 seam is proven, compare
all numerical sections, and update the sample manifest. Deleted product-code
line count in this baseline increment: zero.
