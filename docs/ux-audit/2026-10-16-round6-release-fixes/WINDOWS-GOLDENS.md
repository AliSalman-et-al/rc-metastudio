# Windows golden review — 10 presentation candidates, 4 defects

Reference: PR [#537](https://github.com/AliSalman-et-al/rc-metastudio/pull/537),
head `9caf474aadd98bcd10e205b47628dfd19be95f25`, Windows
[job 116788196931](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/38843274727/job/116788196931).
No golden has been refreshed and no product code has changed in this continuation.
The reviewer permits only demonstrated intended presentation changes; numerical
contracts, tolerances, skips and exceptions remain unchanged.

## Two prerequisites discovered

The job's upload step preserves `artifacts/verification/rcms` only. The R-stack
runner writes its strict capture to
`build/qt6-verification/golden-compatibility-r-stack-v2`, outside that tree.
The log retains the fourteen drift descriptions, not the differing text or image
bytes. The original download inventory and artifact digest are recorded in
[WINDOWS-GOLDENS.json](WINDOWS-GOLDENS.json). Desktop screenshots cannot substitute
for the exact golden PNGs. The complete download contains 9,697 files and zero
strict reports, capture JSONs or `golden_*.png` files. The measured archive digest
matches GitHub's SHA-256 exactly; see `raw/windows-goldens/DOWNLOAD-SHA256.json`.
None of the required old/new image comparisons is
claimed complete. The workflow now uploads that existing capture directory as a
separate `full-r-stack-windows-golden-capture` artifact even on failure, preserving
the desktop upload layout and all verification commands.

The required matching Linux plot-refresh commits also do not exist in rounds
3–6. Inspecting every version of the archive shows **zero plot-hash changes** in
`7afbbbe`, `b7d1437`, `9989f3f`, `2e645c5`, `e4b9824`, and `d747d49`.
Those commits change report text only. Seven plots were last refreshed by
[`74ad86e`](https://github.com/AliSalman-et-al/rc-metastudio/commit/74ad86eef9d7fc0ac3df19fec2487961510d3e2b)
in round 2; subgroup plots by
[`0ada606`](https://github.com/AliSalman-et-al/rc-metastudio/commit/0ada606a0415c1462d4afe093ba90dbff76a3d20)
in round 2; regression plots by `e1c7a88` on 6 September. All archive case metadata
still says Windows; there is one shared archive, not separate Linux/Windows
copies. Linux uses the existing cross-platform descriptor/hash-validity policy,
which does not require equality of image bytes. A passing Linux plot row is
therefore not evidence of a matching plot refresh. The history is reproducible
with [windows_golden_evidence.py](windows_golden_evidence.py).

## Fourteen-drift classification ledger

All eleven old/shared-archive and new/actual-Windows plot pairs were personally inspected. The exact Windows capture reproduces 447 pass / 13 existing accepted exceptions / 14 drift. All eleven PNG hashes validate; its CI merge-ref tree equals `8f5e1f2`, whose production source equals `9caf474`. All 415 original Windows numerical fields are also **exact**, maximum difference zero.

Capture: run [38848117604](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/38848117604), artifact `full-r-stack-windows-golden-capture`, ID `12025995834`, 23,833,977 bytes, GitHub digest `sha256:4dbf2013a713ebd7e312e2268f4984d77b83877ba9db0f91beb2cf176e3d68c9`. Raw files: `raw/windows-goldens/capture-8f5e1f2/`. Exact source/runtime and per-image hashes/dimensions are in [WINDOWS-VISUAL-REVIEW.json](WINDOWS-VISUAL-REVIEW.json).

**None is authorised for refresh yet.** The ten visually intended candidates lack the matching historical Linux plot-refresh commits required by the brief. The diagnostic PNG and three report sections are real defects, requiring product fixes and actual Windows re-verification.

| Case | Drift | Classification / observation | Evidence / presentation implementation commits |
| --- | --- | --- | --- |
| amino-binary-random | Forest Plot | Intended presentation candidate; historical-refresh criterion blocked. Measured grouped headers, clearer numeric/plot separation and conventional displayed-scale label. Nineteen studies, intervals, weights, pooled diamond and footers retained. | [old/new](windows-goldens/amino-binary-random-pair.png) · [difference](windows-goldens/amino-binary-random-diff.png); [`2e645c5`](https://github.com/AliSalman-et-al/rc-metastudio/commit/2e645c5), [`932daed`](https://github.com/AliSalman-et-al/rc-metastudio/commit/932daed), [`443fdec`](https://github.com/AliSalman-et-al/rc-metastudio/commit/443fdec), [`e4b9824`](https://github.com/AliSalman-et-al/rc-metastudio/commit/e4b9824) |
| continuous-random | Forest Plot | Intended presentation candidate; historical-refresh criterion blocked. Measured heading/annotation spacing and conventional axis label; six study rows and pooled interval retained. | [old/new](windows-goldens/continuous-random-pair.png) · [difference](windows-goldens/continuous-random-diff.png); [`2e645c5`](https://github.com/AliSalman-et-al/rc-metastudio/commit/2e645c5), [`932daed`](https://github.com/AliSalman-et-al/rc-metastudio/commit/932daed), [`443fdec`](https://github.com/AliSalman-et-al/rc-metastudio/commit/443fdec), [`e4b9824`](https://github.com/AliSalman-et-al/rc-metastudio/commit/e4b9824) |
| lymph-diagnostic-random-dor | Odds Ratio Forest Plot | Defect: missing U+2080 glyph. Intended header/axis/footer changes coexist with a U+2080 missing-glyph box in the tested-null footer. Enlarged actual PNG confirms it; cannot refresh. | [old/new](windows-goldens/lymph-diagnostic-random-dor-pair.png) · [difference](windows-goldens/lymph-diagnostic-random-dor-diff.png); [`7b537b8`](https://github.com/AliSalman-et-al/rc-metastudio/commit/7b537b8), [`2e645c5`](https://github.com/AliSalman-et-al/rc-metastudio/commit/2e645c5), [`932daed`](https://github.com/AliSalman-et-al/rc-metastudio/commit/932daed), [`443fdec`](https://github.com/AliSalman-et-al/rc-metastudio/commit/443fdec) |
| amino-binary-cumulative | Cumulative Forest Plot | Intended presentation candidate; historical-refresh criterion blocked. Study added (k), tighter rows, bounded dashed null guide and natural-scale metric title; all nineteen row estimates/intervals retained. | [old/new](windows-goldens/amino-binary-cumulative-pair.png) · [difference](windows-goldens/amino-binary-cumulative-diff.png); [`b57fa5e`](https://github.com/AliSalman-et-al/rc-metastudio/commit/b57fa5e), [`27c6023`](https://github.com/AliSalman-et-al/rc-metastudio/commit/27c6023), [`e4b9824`](https://github.com/AliSalman-et-al/rc-metastudio/commit/e4b9824), [`4e8f0e5`](https://github.com/AliSalman-et-al/rc-metastudio/commit/4e8f0e5) |
| amino-binary-leave-one-out | Leave-one-out Forest plot | Intended presentation candidate; historical-refresh criterion blocked. Explicit Study omitted labels, compact rows, bounded null guide and metric title; overall plus nineteen omission fits retained. | [old/new](windows-goldens/amino-binary-leave-one-out-pair.png) · [difference](windows-goldens/amino-binary-leave-one-out-diff.png); [`44e50ae`](https://github.com/AliSalman-et-al/rc-metastudio/commit/44e50ae), [`b57fa5e`](https://github.com/AliSalman-et-al/rc-metastudio/commit/b57fa5e), [`27c6023`](https://github.com/AliSalman-et-al/rc-metastudio/commit/27c6023), [`4e8f0e5`](https://github.com/AliSalman-et-al/rc-metastudio/commit/4e8f0e5) |
| continuous-cumulative | Cumulative Forest Plot | Intended presentation candidate; historical-refresh criterion blocked. Study added (k), bounded null guide and round full-range axis -0.40 to 0.80; six cumulative values retained. | [old/new](windows-goldens/continuous-cumulative-pair.png) · [difference](windows-goldens/continuous-cumulative-diff.png); [`b57fa5e`](https://github.com/AliSalman-et-al/rc-metastudio/commit/b57fa5e), [`27c6023`](https://github.com/AliSalman-et-al/rc-metastudio/commit/27c6023), [`a74cbaf`](https://github.com/AliSalman-et-al/rc-metastudio/commit/a74cbaf), [`4e8f0e5`](https://github.com/AliSalman-et-al/rc-metastudio/commit/4e8f0e5) |
| continuous-leave-one-out | Leave-one-out Forest plot | Intended presentation candidate; historical-refresh criterion blocked. Study omitted labels, bounded null guide and round zero-through-0.70 axis; overall plus six omission values retained. | [old/new](windows-goldens/continuous-leave-one-out-pair.png) · [difference](windows-goldens/continuous-leave-one-out-diff.png); [`44e50ae`](https://github.com/AliSalman-et-al/rc-metastudio/commit/44e50ae), [`b57fa5e`](https://github.com/AliSalman-et-al/rc-metastudio/commit/b57fa5e), [`27c6023`](https://github.com/AliSalman-et-al/rc-metastudio/commit/27c6023), [`4e8f0e5`](https://github.com/AliSalman-et-al/rc-metastudio/commit/4e8f0e5) |
| amino-binary-meta-regression | Regression Plot | Intended presentation candidate; historical-refresh criterion blocked. Full displayed prediction range, round log-scale tick values, natural metric title and grid/null-guide treatment; study bubbles and fitted/prediction curves retained. | [old/new](windows-goldens/amino-binary-meta-regression-pair.png) · [difference](windows-goldens/amino-binary-meta-regression-diff.png); [`0a979bb`](https://github.com/AliSalman-et-al/rc-metastudio/commit/0a979bb), [`a74cbaf`](https://github.com/AliSalman-et-al/rc-metastudio/commit/a74cbaf), [`d3d2366`](https://github.com/AliSalman-et-al/rc-metastudio/commit/d3d2366), [`76e0d13`](https://github.com/AliSalman-et-al/rc-metastudio/commit/76e0d13), [`2450544`](https://github.com/AliSalman-et-al/rc-metastudio/commit/2450544), [`4e8f0e5`](https://github.com/AliSalman-et-al/rc-metastudio/commit/4e8f0e5) |
| continuous-meta-regression | Regression Plot | Intended presentation candidate; historical-refresh criterion blocked. Full prediction range including negative lower band, round ticks and bounded/null-guide treatment; six bubbles and model/prediction curves retained. | [old/new](windows-goldens/continuous-meta-regression-pair.png) · [difference](windows-goldens/continuous-meta-regression-diff.png); [`0a979bb`](https://github.com/AliSalman-et-al/rc-metastudio/commit/0a979bb), [`a74cbaf`](https://github.com/AliSalman-et-al/rc-metastudio/commit/a74cbaf), [`d3d2366`](https://github.com/AliSalman-et-al/rc-metastudio/commit/d3d2366), [`76e0d13`](https://github.com/AliSalman-et-al/rc-metastudio/commit/76e0d13), [`2450544`](https://github.com/AliSalman-et-al/rc-metastudio/commit/2450544), [`4e8f0e5`](https://github.com/AliSalman-et-al/rc-metastudio/commit/4e8f0e5) |
| amino-binary-subgroup | Subgroup Forest Plot | Intended presentation candidate; historical-refresh criterion blocked. Compact subgroup density, complete arm/effect headers, bounded null guides and natural metric title; both groups, totals, within-group/overall diamonds and difference test retained. | [old/new](windows-goldens/amino-binary-subgroup-pair.png) · [difference](windows-goldens/amino-binary-subgroup-diff.png); [`76d9f62`](https://github.com/AliSalman-et-al/rc-metastudio/commit/76d9f62), [`27c6023`](https://github.com/AliSalman-et-al/rc-metastudio/commit/27c6023), [`09a29de`](https://github.com/AliSalman-et-al/rc-metastudio/commit/09a29de), [`e4b9824`](https://github.com/AliSalman-et-al/rc-metastudio/commit/e4b9824), [`4e8f0e5`](https://github.com/AliSalman-et-al/rc-metastudio/commit/4e8f0e5), [`443fdec`](https://github.com/AliSalman-et-al/rc-metastudio/commit/443fdec) |
| continuous-subgroup | Subgroups Forest Plot | Intended presentation candidate; historical-refresh criterion blocked. Compact subgroup density, explicit effect header, bounded null guides and round axis; both groups, weights, diamonds and comparison footer retained. | [old/new](windows-goldens/continuous-subgroup-pair.png) · [difference](windows-goldens/continuous-subgroup-diff.png); [`76d9f62`](https://github.com/AliSalman-et-al/rc-metastudio/commit/76d9f62), [`27c6023`](https://github.com/AliSalman-et-al/rc-metastudio/commit/27c6023), [`09a29de`](https://github.com/AliSalman-et-al/rc-metastudio/commit/09a29de), [`e4b9824`](https://github.com/AliSalman-et-al/rc-metastudio/commit/e4b9824), [`4e8f0e5`](https://github.com/AliSalman-et-al/rc-metastudio/commit/4e8f0e5) |
| lymph-diagnostic-random-dor | Odds Ratio Summary | **Defect:** Windows native-locale character loss (τ² → t² and H₀ → H0); numbers identical. | [Exact text diff](windows-goldens/lymph-diagnostic-random-dor-text.diff); shared Linux text last refreshed `2e645c5` |
| amino-binary-subgroup | Subgroup Summary | **Defect:** Windows native-locale character loss (τ² → t²); numbers identical. | [Exact text diff](windows-goldens/amino-binary-subgroup-text.diff); shared Linux text last refreshed `e4b9824` |
| continuous-subgroup | Subgroup Summary | **Defect:** Windows native-locale character loss (τ² → t²); numbers identical. | [Exact text diff](windows-goldens/continuous-subgroup-text.diff); shared Linux text last refreshed `d747d49` |

The source commits above explain presentation behavior; **they are not Linux plot-refresh commits**. Last plot refresh remains round-two `74ad86e` for seven, round-two `0ada606` for two subgroup plots, September `e1c7a88` for two regressions. There is no separate stale Windows report copy: all three fresh Linux sections equal the shared archive byte-for-byte.

The [enlarged diagnostic footer](windows-goldens/lymph-missing-subscript.png) visibly contains a U+2080 missing-glyph box. The Windows SVG contains the intended `H₀` text and declares primary Arial only; the failure occurs in rendering/export, separately from the report strings which lose the character before display. This PNG cannot be blessed. The other ten pairs have readable glyphs/rows, the intended metric/header/density/axis/null-guide changes, and no observed clipping or missing plot component. All eleven current Linux-vs-Windows pairs were also personally inspected: the same components and values are present, with ordinary native font/device metric variance. The diagnostic U+2080 box is the sole observed rendering defect. Those pairs and observations are linked from WINDOWS-VISUAL-REVIEW.json.

The three report defects are addressed in the pending product change: S3 format methods build Unicode text directly and pad by display width, retaining print methods but removing the application console-capture roundtrip. The stronger real-R/production-bridge test failed before implementation and now passes under a deliberately non-Unicode locale, with all three actual report texts equal between C and UTF-8 Linux captures. All eleven Linux report texts and PNG hashes are identical before/after this fix. See [WINDOWS-REPORT-FIX.json](WINDOWS-REPORT-FIX.json). Actual post-fix Windows proof remains due; no text golden refresh is authorised or needed.

The diagnostic glyph repair is planned before implementation in PLAN.md. It must preserve Unicode caption text, normal primary typography, numerical values and the existing SVG identity checks, then produce a personally inspected glyph-correct actual Windows PNG.

### Policy decision still required for presentation candidates

The requested historical Linux plot refresh evidence does not exist. A reviewer must explicitly permit the alternative of same-production Linux captures plus personally inspected old/new Windows diffs (and a post-fix Windows check for the diagnostic plot) before any candidate is refreshed. No numerical oracle, tolerance, skip or exception change is proposed. If this prerequisite is retained, the release remains blocked; do not invent a matching commit or merge on a descriptor-only Linux pass.

## Commands and observed results

Run from the repository root. Original artifact metadata identifies
`full-r-stack-windows-evidence`, ID `12023705674`, 676,737,347 bytes, GitHub digest
`sha256:7ec2803a38e802b52c387271c03e03bf4bd190a0a241a23d86dac6db1b3f146a`.

```bash
evidence=docs/ux-audit/2026-10-16-round6-release-fixes/raw/windows-goldens
gh api repos/AliSalman-et-al/rc-metastudio/actions/artifacts/12023705674 > "$evidence/artifact.json"
gh run download 38843274727 --name full-r-stack-windows-evidence --dir "$evidence/ci"
gh run view 38843274727 --job 116788196931 --log > "$evidence/job.log"
source docs/ux-audit/2026-10-14-round3/ENV.sh
uv run python scripts/verify_golden_compatibility.py --output-root build/qt6-verification/golden-compatibility-windows-review-linux > "$evidence/linux-strict.log" 2>&1
RCMS_AUDIT_DIR="$evidence" uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-windows-review-linux
uv run python docs/ux-audit/2026-10-16-round6-release-fixes/windows_golden_evidence.py --ci "$evidence/ci" --linux build/qt6-verification/golden-compatibility-windows-review-linux --output docs/ux-audit/2026-10-16-round6-release-fixes
```

Fresh Linux strict gate: exit 0, 461 pass / 13 existing accepted exceptions /
zero drift, eleven cases and 474 comparison rows. Numerical replay: exit 0,
**415 original fields exactly unchanged; maximum difference 0**; all original
numerical contracts, tolerances and exceptions unchanged. The three named report
sections equal the archive exactly. Linux uses the pinned test-owned R 4.6.1
runtime and retained library selected by ENV.sh; this is not Windows qualification.

Downloaded complete job log: 1,032,383 bytes, 8,742 lines, SHA-256
`41a9f6663c2556c7bb05310d5c8cf653d15f49f792f10ee3a6682e82319b19d7`.
It confirms R CMD check Status OK, nine bridge checks passed, 123 desktop checks
passed, then strict-golden exit 1. The original final-head snapshot remains
10 checks passed / 2 failed in
`raw/lexer/checks-9caf474-final.json`. No merge or post-merge verification has
occurred. Continue with the new Windows capture before classifying or refreshing.

Workflow validation: PyYAML parsed the modified workflow; the strict-capture
upload runs under `always()`, its path equals the runner's existing output path,
and the desktop upload path and full-R command remain unchanged. `git diff
--check` passed. This is evidence retention only; no gate, analysis, oracle or
package behavior changes.
