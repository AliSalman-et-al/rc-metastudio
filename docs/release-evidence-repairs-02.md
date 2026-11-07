# Release evidence repair batch 02

Base: `c27e6d6c`, preserving `d26f46d0`. Evidence is retained, ignored, under
`artifacts/fixes/release-evidence-02/` in the implementation worktree. No R source,
reference runtime/library, release workflow, publication helper or user state was changed.

## Dispositions and proof

Each row is a source/contract repair, not native package qualification.

| Canonical ID | Before | After and proof |
| --- | --- | --- |
| G4A-006 | Assembler emitted passing evidence for failed samples; extracted Windows gate ignored them. | Assembler rejects failed aggregate/records before output; extracted gate independently checks them. Complete assembler controls accepted by both inspectors, aggregate/record mutations rejected. Community and trusted workflows call this assembler and check its nonzero exit; workflows were source-traced, not dispatched. |
| G4B-007 | Later malformed field/changelog or failed write left mixed versions. | Preflight every replacement and changelog; exact-byte backups restore on write error. Failed rollback retains numbered originals and paths.json for recovery. Late-field, changelog and injected write failure controls pass; rollback-failure retention is source-inspected, not fault-injected. |
| G4B-008 | First-only replacement hid duplicate fields. | Count every match and require exactly one. Duplicate fixture rejected without any writes. |
| G4B-009 | Impossible shaped dates accepted. | Calendar parser rejects February 30; leap-day positive control passes. All version tests use disposable copies. |
| G4B-010 | Direct Windows helper calls depended on caller directory. | All nine helper invocations resolve through repoRoot. PowerShell AST argument evaluation from TEMP fails on baseline, passes after repair; no full executable build claimed. |
| G4B-011 | Linux tar/macOS ZIP became final before qualification; startup cleared previous final files. | Candidate bytes and failed diagnostics stay in unique candidate directories; promote only after inspection/qualification/evidence succeed. Real Bash with disposable archives/command stand-ins preserves prior final bytes on Linux smoke and macOS inspection failure. Explicit SkipSmoke behavior remains opt-out, not qualified evidence. |
| G4E-006 | Matching hashes accepted unrelated diagnostic placeholders. | Standalone validation parses phases, package smoke values/paths, graph identity/native inventory and quarantine identity. Complete historical offline fixture passes; independently rehashed unrelated diagnostics fail. No historical host paths need to exist. Native loader execution remains unproved. |
| G4E-007 | Lexically relative retained paths escaped through symlinks. | Resolve root and target, reject escapes/resolution errors; diagnostic paths use same containment check. Actual symlink escape reproduced then rejected. |
| G4F-001 | Fixed temporary DMG name could alias and delete input. | Unique private output directory owns temporary DMG. Baseline command-stand-in failure deleted disposable input; repaired failure preserves exact bytes. |
| G4F-002 | Multiple attached mount points failed validation before detach cleanup. | Record all mount points before single-volume validation; EXIT detaches every owned point. Two-volume command stand-in records both detaches. No real mounts or service calls. |
| G4F-004 | Probe digest could identify a different kit; basename matching admitted displaced paths. | Compare probe and manifest kit digests; compare resolved probe files and byte digests with packaged derivation. Positive controls plus different digest and displaced same-basename controls pass. No native kit installation/loader qualification. |
| G4F-005 | Manifest omission prevented a shipped sample from being opened. | Capture reconciles full shipped rcms inventory, unique manifest entries, contained paths and hashes before launching. macOS qualification reconciles original and extracted observations with authenticated deployment sample paths/hashes and manifest hash. Omission control rejected. |
| G4F-006 | Same-source extracted evidence could describe different app bytes. | Compare complete original/extracted file records before qualification; existing archive inspection authenticates original inventory bytes. Single digest mutation rejected. No actual macOS archive build. |
| G4F-008 | R installer wait was unlimited. | Existing owned-tree watchdog bounds installer at 900s; retained watchdog/installer logs survive registry finally restoration. Production watchdog command with a sleeping dummy at 1s reaches exit 124. No installer/registry mutation or system installation performed. Registry restore is existing code, not re-proved here. |
| G5C-001 | Windows symlink fixture could fail before pruning. | Skip only explicit Windows privilege error 1314; other failures propagate. Actual symlink-capable Windows pruning test passes. Privilege-denied branch is not exercised on this capable host. |
| G5C-002 | Later successful shell commands masked intermediate identity checks. | Required standalone comparisons explicitly exit 35. Injected incorrect intermediate identity is rejected; ordinary restoration control passes. |
| G5C-003 | Incomplete malformed ZIPs could fail for missing members. | Add hostile members to a complete valid fixture and match each diagnostic. Traversal/backslash/collision guard mutants each produce intended DID NOT RAISE failures. Raw ZIP spelling is checked before Windows ZipInfo normalization. |
| G5C-004 | Darwin binary fixture always named archive zip. | Fixture and evidence assertions choose tgz on Darwin, zip on Windows. Actual Windows native R policy test passes; Darwin execution unavailable. Production R policy unchanged. |

## Qualification

Run `uv sync --locked`, set `RCMS_QT6_RCC` to the parent pinned rcc, then
`uv run python scripts/build_qt6.py generate --build-root build/qt6-verification`.
The repository-wide typing invocation is:

```
uv run python -c "from scripts.verify import run_typing; from pathlib import Path; run_typing(Path('build/qt6-verification'))"
```

It expands to full strict Ty targeting win32 with all generated-module search paths;
initial and final transcripts retain the expanded command. It passed before GUI imports.

With `RCMS_QT6_BUILD_ROOT` selecting that build and `QT_QPA_PLATFORM=offscreen`:

```
uv run python -m pytest tests/packaging/contract tests/python/fast/test_qt6_macos_feasibility.py tests/python/fast/test_rcmetar_r_manifest_validation.py tests/python/fast/test_packaged_automation_dispatch.py -q --basetemp=artifacts/fixes/release-evidence-02/qualification-final-2
```

Result: 189 passed, 1 skipped, exit 0. The skip was the pre-existing real-R marker
probe because Rscript was absent from PATH; selecting R 4.6.1/bin and rerunning that
probe separately passed (marker-native-r.log). The R policy fixture uses actual R;
no statistical package execution or runtime-04 installed-source equivalence is claimed.

Failure-first transcripts include before-release.log (8 failed, 1 positive passed),
before-identities.log (3 intended failures), before-diagnostics.log, shell-before.log
and helper-paths-before.log. Failed attempts remain retained: missing generated-root
environment, initial placeholder sample inputs, Windows ZIP normalization, missing
Python3 shim, and Windows PowerShell stderr handling were corrected and rerun.
The final proof does not retroactively turn those attempts into successful runs.

Additional reproducible scripts/transcripts: helper-paths.ps1, installer-watchdog.ps1,
zip-mutations.py, shell-retention.log, qualification-recovery.log. inputs, exact shell
drives, stdout/stderr and return codes remain in the unique pytest evidence directories.

## Compatibility and limits

Malformed/duplicate version metadata, invalid dates, incomplete or inconsistent sample,
kit, inventory and diagnostic evidence now fail closed. Normal output names and successful
release formats remain unchanged. Failed candidates intentionally remain for inspection.
This is not a multi-file crash-atomic version transaction; write exceptions are rolled back.
Recovery from an OS crash/power failure and failed rollback needs the retained backups.

No macOS/Linux native package qualification, real mounting, Developer ID signing,
notarization, workflow dispatch, publication, push or PR occurred. Windows helper and
installer evidence covers argument resolution and owned-process control, not an actual
Windows distributable build. Parent owns aggregate full-profile/integration qualification.
