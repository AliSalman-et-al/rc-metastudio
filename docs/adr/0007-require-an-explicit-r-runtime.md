# Require an explicit R runtime

Status: Superseded by [ADR 0012](0012-supervise-a-persistent-r-worker.md).

Production startup constructs one real R runtime and fails with a typed actionable error when it cannot start; it never installs a fabricated backend after catching an arbitrary exception. Tests may provide explicit local fakes at narrow application seams, accepting a small amount of test composition in exchange for eliminating plausible but false statistical behavior from production.

The Windows worker environment carries the variables required by R and its
packages even when launched from a minimal caller environment. In particular,
the cli package needs the Windows system path variable at shutdown. Frozen
bootstrap must set HOME before Qt resolves its application-data location.
