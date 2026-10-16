# Windows golden review — evidence recovery in progress

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

These are pending classifications, **not permission to refresh**. The next
Windows capture must be reviewed first; if plots are otherwise intended, the
missing Linux-refresh prerequisite still requires a reviewer decision.

| Case | Drift | Current classification | Evidence / last archive presentation update |
| --- | --- | --- | --- |
| amino-binary-random | Forest Plot | Pending exact Windows PNG / visual inspection | Plot: `74ad86e` (round 2); no round 3–6 plot refresh |
| continuous-random | Forest Plot | Pending exact Windows PNG / visual inspection | Plot: `74ad86e` (round 2); no round 3–6 plot refresh |
| lymph-diagnostic-random-dor | Odds Ratio Forest Plot | Pending exact Windows PNG / visual inspection | Plot: `74ad86e` (round 2); no round 3–6 plot refresh |
| amino-binary-cumulative | Cumulative Forest Plot | Pending exact Windows PNG / visual inspection | Plot: `74ad86e` (round 2); no round 3–6 plot refresh |
| amino-binary-leave-one-out | Leave-one-out Forest plot | Pending exact Windows PNG / visual inspection | Plot: `74ad86e` (round 2); no round 3–6 plot refresh |
| continuous-cumulative | Cumulative Forest Plot | Pending exact Windows PNG / visual inspection | Plot: `74ad86e` (round 2); no round 3–6 plot refresh |
| continuous-leave-one-out | Leave-one-out Forest plot | Pending exact Windows PNG / visual inspection | Plot: `74ad86e` (round 2); no round 3–6 plot refresh |
| amino-binary-meta-regression | Regression Plot | Pending exact Windows PNG / visual inspection | Plot: `e1c7a88` (6 September); no round 3–6 plot refresh |
| continuous-meta-regression | Regression Plot | Pending exact Windows PNG / visual inspection | Plot: `e1c7a88` (6 September); no round 3–6 plot refresh |
| amino-binary-subgroup | Subgroup Forest Plot | Pending exact Windows PNG / visual inspection | Plot: `0ada606` (round 2); no round 3–6 plot refresh |
| continuous-subgroup | Subgroups Forest Plot | Pending exact Windows PNG / visual inspection | Plot: `0ada606` (round 2); no round 3–6 plot refresh |
| lymph-diagnostic-random-dor | Odds Ratio Summary | Presumptive Windows defect; raw text needed for diagnosis | Linux text equals current archive exactly; last text refresh `2e645c5` |
| amino-binary-subgroup | Subgroup Summary | Presumptive Windows defect; raw text needed for diagnosis | Linux text equals current archive exactly; last text refresh `e4b9824` |
| continuous-subgroup | Subgroup Summary | Presumptive Windows defect; raw text needed for diagnosis | Linux text equals current archive exactly; last text refresh `d747d49` |

No visual diff links can honestly be supplied until the actual Windows golden
PNGs are available. Old archive images were extracted to
`raw/windows-goldens/old-images/`; they have not been paired with substitute
desktop images or approved for refresh. The three Windows-only report differences
cannot be stale separate Windows copies: there is only one archive, and all three
fresh Linux sections equal it byte-for-byte. Their exact Windows text is needed
to diagnose product encoding, formatting or other causes.

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
