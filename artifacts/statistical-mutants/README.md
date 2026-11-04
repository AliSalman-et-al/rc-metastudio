# Targeted mutation proof

Run from the repository root: bash artifacts/statistical-mutants/prove.sh.
Environment and exact per-command traces are retained alongside this file.
Ty targets win32; desktop evidence uses Linux Qt offscreen, not release qualification.

Coverage gaps:
- continuous.fixed authority cases used only z; binary.random owned the inference selector loop. Added three independent metafor FE comparisons on six entered estimates, including p-values and both CI bounds. R code is in analysis_authorities.R; its JSON records actual/expected values, R and pinned package versions. No frozen values changed.
- Raw IRR transient previews had no independent interval comparison. Added a direct metafor comparison in the existing sheets desktop drive, with counts 4/9, times 100/120 (variance .361111..., far from one). The step retains R code, inputs and both results; runtime.json records package versions. This checks the bridge boundary, not the separate pooled-analysis path.
- The XLSX wizard always passes column_mapping, bypassing the fallback. Existing mapped date-year coverage therefore cannot detect it. Added a no-mapping date-year case to the existing parser test module; expected output is calendar year 2022. No new unit-test module or GUI entry point was invented.
