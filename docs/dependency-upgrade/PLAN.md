# Dependency upgrade

Update Python and R runtimes, direct and transitive libraries, test/build tools,
CI, and package provenance to a stable combination supported on Windows x64,
Apple silicon macOS, and Ubuntu 24.04 x86_64. Preserve the existing binary-only
R package policy and exact reproducible versions. The approved About and shell
cleanup changes predate this upgrade and must remain intact.

Start from a working pinned-runtime baseline. Then upgrade Python and R in
separate verifiable units. Retain commands, inputs, runtime identities, logs,
lockfile/manifests, old and new numerical outputs, and independent comparisons.

The user authorizes fixture changes for independently validated improvements in
upstream statistical calculations. A version bump alone is not proof. For each
changed result, explain the method and upstream change, compare direct package
calls and independent references, then record why the new result is correct.
Do not hide differences by widening tolerances or bulk-regenerating baselines.

Required proof: strict typing, real R package checks, independent statistical
comparisons, frozen result comparisons with justified reviewed updates, complete
desktop regression matrix, affected native workflows, and platform packaging
checks. Opus 5.5 Medium must approve any GUI changes. Clearly identify any target
that cannot be qualified on the available hosts.

Candidate: Python 3.14.10, R 4.6.2, Qt 6.12.0, rpy2 3.6.9, and
Posit snapshot 2026-11-13. All 151 binary dependency versions, including the
recommended-package closure, agree across the three target indices. Metafor
moves from 5.0-1 to 5.2-1; meta 8.5-0 and mada 0.5.12 remain current. The binary
installer also replaces outdated recommended packages: R 4.6.2 bundles mgcv
1.9-4 and nlme 3.1-171, while the snapshot provides 1.9-5 and 3.1-172.

Ty 0.0.102 is required. The user explicitly requested the typing cleanup after
the newest checker reported 751 diagnostics. Follow Astral recommended rule defaults with warnings fatal, replace
obsolete Qt stub workarounds, specify real container shapes, and fix unsafe
narrowing and overrides without blanket suppressions or broad Any annotations.
PyQt6-Pdf 6.140.0 is explicit in dev dependencies because Qt 6.12
separates the PDF module used by export verification.

Status: latest ty 0.0.102 typing gate passes; workspace environment and candidate
lock updated. The original Python/R stack passes the frozen 11-case oracle,
including all 416 numerical fields, and 103 independent authority comparisons.
The final R scientific gates and unchanged frozen oracle pass. Opus 5.5 Medium
approves the GUI. The expanded typing gate includes the skill drivers and passes;
the rebuilt package passes. The final desktop matrix completed with 129 passes
and four driver failures. All four failing paths pass targeted recovery; HR
and funnel controls pass too. IRR completed in 610.46 seconds with a scoped
1,200-second verification allowance after two 600-second timeouts. All 133
desktop obligations have passing evidence, with 17,817 retained artifact hashes
verified. The original full command remains failed; the composed qualification
and native-platform/timing limits are recorded in RESULTS.md. Application and
numerical behavior are unchanged by the driver recovery.
Frozen fixtures remain unchanged.

User steering: follow Astral best practices. Remove all=error (which opts into
every optional rule), use recommended defaults with warnings fatal, and clean up
all remaining diagnostics on ty0.0.102. Apply pstack with one canonical decision
trail and bounded, failure-driven verification/review.
