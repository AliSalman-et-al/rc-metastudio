# PR 558 sequential assertion follow-up

Product semantics: a leave-one-out row is the pooled fit without the named study, not that study's individual effect. Omitting a double-zero study therefore retains a finite pooled estimate/CI. Cumulative rows likewise describe prefix fits; subgroup summaries describe within-group pools. The standard study-level double-zero assertion cannot apply to these workflows.

Only code change: require `workflow == "standard"` before the MH/Peto study-level display assertion in analysis_matrix.py. No R/product/r_bridge changes.

## Failed CI evidence

Downloaded GitHub Actions run 41824250848 artifact 13318798629 (`full-r-stack-windows-2-evidence`), job 126554983109. The selected original SVG, copied report, steps and stderr are retained in ci-failure/.

Both SVG and copied report contain zero `Not estimable` strings. MH's Tulkens and Vanhaeverbeek omission rows both show 0.711969 [0.542864, 0.933750], equal to the full pool, as expected. The only failure is the assertion requiring two study-level Not estimable rows in this pooled-fit table.

`rcmetar.build.sequential.metafor.bundle()` derives display values from each result's b/ci.lb/ci.ub; it does not call the changed standard.plot.fields eligibility masking. `_insert_held_effects()` receives those finite pooled display values, so its NA-to-Not-estimable formatting never applies to these rows. Retained local cumulative and leave-one-out SVGs and copied reports also contain no Not estimable labels. Subgroup individual study rows may legitimately be Not estimable; subgroup pooled rows remain finite, checked independently by the existing public-metafor oracle.

## Local qualification

Source `/home/ali/.t3/qa-env/ENV.sh`; export `PYTHONPATH=$PWD/src:$PWD`, prepend `$PWD/build/rcmetar-lib` to RCMS_R_LIBS and R_LIBS. Strict typing (win32) ran before GUI qualification; exact command and pass transcript in typing.log.

Run `python scripts/verify_rcms.py <scenario>` for each:
- analysis-sequential-fixed-leave-one-out
- analysis-sequential-fixed-cumulative
- analysis-sequential-fixed-subgroup
- analysis-binary.fixed.mh
- analysis-binary.fixed.peto

Each command log identifies its full durable evidence directory under artifacts/verification/rcms, containing manifest, runtime identity, fixture inputs, action/results, SVGs, report exports and numerical oracle receipts. The three sequential runs cover MH, Peto and continuous fixed inverse variance; displayed estimate/CI/SE values match independent public-metafor fits within the existing 1e-6 tolerance. The standard MH/Peto scenarios retain the double-zero display and footer assertions.

Manuscript-export failures are excluded at the user's direction: pre-existing master viewport breakage handled by a separate PR. No merge performed.
