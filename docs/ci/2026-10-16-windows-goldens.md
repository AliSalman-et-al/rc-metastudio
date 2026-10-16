# Windows presentation goldens after 0.5.0

Base: `29084f0` (PR #537). Original failure: [run 38843274727](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/38843274727/job/116788196931).

The original job omitted strict capture bytes. Its same-production recovery,
[run 38848117604](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/38848117604),
retains artifact `12025995834` (SHA-256 `4dbf2013a713ebd7e312e2268f4984d77b83877ba9db0f91beb2cf176e3d68c9`).
I personally inspected all eleven linked old/new Windows pairs. Ten contain only
intended presentation changes; the diagnostic footer also has a real missing glyph.

There were no Linux plot-hash refreshes in rounds 3–6: the shared archive changed
report text only, and Linux accepts cross-platform plot descriptors. The user
said “Use best judgement” after this discrepancy was explained. Same-source
Linux/Windows captures and reviewed old/new Windows images establish intent;
Linux passing alone does not. Existing detailed history and hashes:
[visual review](../ux-audit/2026-10-16-round6-release-fixes/WINDOWS-VISUAL-REVIEW.json).

The three text defects were already repaired by `d52162d`; diagnostic SVG font
fallback by `d3c5030`, both included in the squash. No report text refresh is permitted.
Fresh [Windows run 38854829785](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/38854829785/job/116824109778)
checked out `6a5c7d1`, whose entire tree equals `29084f0`. R CMD check: OK;
nine bridge contracts and 123 desktop scenarios passed. Strict: 450 pass,
13 existing exceptions, eleven plot drifts; all three report defects pass.
All 415 original numerical fields are exact. Ten PNGs match the inspected older
capture byte-for-byte; I inspected the new [diagnostic PNG](2026-10-16-windows-goldens/diagnostic-fixed.png):
H₀ renders correctly, with the intended layout and unchanged rows/values.

The sanctioned `scripts/regenerate_golden_presentation.py` refreshed eleven PNGs
from artifact `12028590487` (digest in [metadata](2026-10-16-windows-goldens/windows-artifact.json)).
Only hash-verified `bundle_path` locations were relocated in a working copy;
downloaded captures were preserved. No text was refreshed. Replay of the unchanged
actual Windows manifest through the existing strict comparator: **461 pass,
13 existing accepted exceptions, zero drift**. Archive audit confirms every text,
numerical output and non-hash case metadata is unchanged. Hash bindings alone
changed in the numerical/plot contracts; tolerances, descriptors and exceptions
remain frozen. Evidence: [Windows replay](2026-10-16-windows-goldens/windows-strict-replay.json),
[visual provenance](2026-10-16-windows-goldens/windows-visual-provenance.json).

| Case | Drift | Classification / observation | Evidence | Commit |
| --- | --- | --- | --- | --- |
| amino-binary-random | Forest Plot | Intended: Measured grouped headers, clearer numeric/plot separation and conventional displayed-scale label. Nineteen studies, intervals, weights, pooled diamond and footers retained. | [old/new](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/amino-binary-random-pair.png) · [difference](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/amino-binary-random-diff.png) | 29084f0 (presentation history linked) |
| continuous-random | Forest Plot | Intended: Measured heading/annotation spacing and conventional axis label; six study rows and pooled interval retained. | [old/new](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/continuous-random-pair.png) · [difference](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/continuous-random-diff.png) | 29084f0 (presentation history linked) |
| lymph-diagnostic-random-dor | Odds Ratio Forest Plot | Defect repaired by merged SVG font fallback; fresh Windows H₀ inspected. Intended header/axis/footer presentation refreshed. | [old/new](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/lymph-diagnostic-random-dor-pair.png) · [difference](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/lymph-diagnostic-random-dor-diff.png) | d3c5030 (repair); 29084f0 |
| amino-binary-cumulative | Cumulative Forest Plot | Intended: Study added (k), tighter rows, bounded dashed null guide and natural-scale metric title; all nineteen row estimates/intervals retained. | [old/new](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/amino-binary-cumulative-pair.png) · [difference](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/amino-binary-cumulative-diff.png) | 29084f0 (presentation history linked) |
| amino-binary-leave-one-out | Leave-one-out Forest plot | Intended: Explicit Study omitted labels, compact rows, bounded null guide and metric title; overall plus nineteen omission fits retained. | [old/new](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/amino-binary-leave-one-out-pair.png) · [difference](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/amino-binary-leave-one-out-diff.png) | 29084f0 (presentation history linked) |
| continuous-cumulative | Cumulative Forest Plot | Intended: Study added (k), bounded null guide and round full-range axis -0.40 to 0.80; six cumulative values retained. | [old/new](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/continuous-cumulative-pair.png) · [difference](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/continuous-cumulative-diff.png) | 29084f0 (presentation history linked) |
| continuous-leave-one-out | Leave-one-out Forest plot | Intended: Study omitted labels, bounded null guide and round zero-through-0.70 axis; overall plus six omission values retained. | [old/new](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/continuous-leave-one-out-pair.png) · [difference](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/continuous-leave-one-out-diff.png) | 29084f0 (presentation history linked) |
| amino-binary-meta-regression | Regression Plot | Intended: Full displayed prediction range, round log-scale tick values, natural metric title and grid/null-guide treatment; study bubbles and fitted/prediction curves retained. | [old/new](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/amino-binary-meta-regression-pair.png) · [difference](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/amino-binary-meta-regression-diff.png) | 29084f0 (presentation history linked) |
| continuous-meta-regression | Regression Plot | Intended: Full prediction range including negative lower band, round ticks and bounded/null-guide treatment; six bubbles and model/prediction curves retained. | [old/new](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/continuous-meta-regression-pair.png) · [difference](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/continuous-meta-regression-diff.png) | 29084f0 (presentation history linked) |
| amino-binary-subgroup | Subgroup Forest Plot | Intended: Compact subgroup density, complete arm/effect headers, bounded null guides and natural metric title; both groups, totals, within-group/overall diamonds and difference test retained. | [old/new](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/amino-binary-subgroup-pair.png) · [difference](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/amino-binary-subgroup-diff.png) | 29084f0 (presentation history linked) |
| continuous-subgroup | Subgroups Forest Plot | Intended: Compact subgroup density, explicit effect header, bounded null guides and round axis; both groups, weights, diamonds and comparison footer retained. | [old/new](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/continuous-subgroup-pair.png) · [difference](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/continuous-subgroup-diff.png) | 29084f0 (presentation history linked) |
| lymph-diagnostic-random-dor | Odds Ratio Summary | **Defect:** Windows native-locale character loss (τ² → t² and H₀ → H0); numbers identical. | [Exact text diff](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/lymph-diagnostic-random-dor-text.diff) | d52162d; 29084f0 |
| amino-binary-subgroup | Subgroup Summary | **Defect:** Windows native-locale character loss (τ² → t²); numbers identical. | [Exact text diff](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/amino-binary-subgroup-text.diff) | d52162d; 29084f0 |
| continuous-subgroup | Subgroup Summary | **Defect:** Windows native-locale character loss (τ² → t²); numbers identical. | [Exact text diff](../ux-audit/2026-10-16-round6-release-fixes/windows-goldens/continuous-subgroup-text.diff) | d52162d; 29084f0 |

## Repeatable verification

```bash
source docs/ux-audit/2026-10-14-round3/ENV.sh
gh run download 38854829785 --name full-r-stack-windows-golden-capture --dir build/qt6-verification/windows-golden-review/download-0644ca2
uv run python scripts/regenerate_golden_presentation.py build/qt6-verification/windows-golden-review/reviewed-0644ca2
uv run python scripts/verify_golden_compatibility.py --root . --output-root build/qt6-verification/golden-compatibility-ci-windows-refreshed
RCMS_AUDIT_DIR=docs/ci/2026-10-16-windows-goldens uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-ci-windows-refreshed
```

The refresh command above used a copy of the download with only the eleven
`captures/*.json` artifact `bundle_path` values replaced by local absolute paths;
[relocation ledger](2026-10-16-windows-goldens/capture-relocation.json) records both paths and verified SHA-256.
Run the comparator before refreshing, inspect every drift, then refresh; this is
an evidence record, not permission to bless arbitrary future output.

Local Linux strict before refresh: 461 pass / 13 exceptions / zero drift;
415 fields exact. Local post-refresh: **461 pass / 13 exceptions / zero drift; 415 fields exact**, maximum difference zero. PR CI is pending.
