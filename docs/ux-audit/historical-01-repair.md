# Historical-01 bounded repair handoff

Base: `f6ffae40`. Scope is historical executable drivers, not current-product qualification. No historical receipts, screenshots, numeric references, R sources or reference libraries were regenerated. No publication, installation or real-service probes were performed.

## Dispositions

| ID | Repair and observed contract |
| --- | --- |
| G7A-001 | Removed the unproved nonzero curve exception in `artifacts/batch7-windows/check_windows.py`; `apply_windows.py` now runs the checker before consuming its receipt. A synthetic nonzero curve score with seven unchanged circle centres fails; the parent accepted it. Archived 0.000543569 mismatch is preserved, not newly qualified. Strict zero within the existing two-pixel matcher is now required. |
| G7A-002 | `artifacts/batch7-review/prove-goldens.py` requires equal unique archive members, equal unique ordered case IDs, strict pairing, and a derived count. Equal one-case fixture passes; omitted case, substituted ID and extra binary fail. Numerical fixture estimate stays exactly 1; frozen real values untouched. |
| G7A-003 | `artifacts/qa-r1/shard-repair/replay.py` always executes the selected scenarios in a fresh `runs/replay-*` directory. Fixture: 23 executions and another 23 on rerun, with original receipts and logs unchanged. Parent review removed the unnecessary resume/cache identity mechanism. |
| G7A-004 | `artifacts/statistical-mutants/prove.sh` delegates its mutant phase to same-root `mutate.py`. Exact existing regular-file preimages are persisted before apply, restored in finally (including handled INT/TERM), and recovery retained on exceptional restoration. Disposable git fixture proves exit 0 and exit 7 restore exact LF bytes and preserve unrelated dirty bytes. Original shell driver demonstrably leaves mutant CRLF bytes after unexpected pass. |
| G7A-005 | `docs/ux-audit/2026-10-13-implementation/collect-finish-evidence.py` verifies copied destination manifest bytes and every destination file digest before recording it. Matching copy passes; corrupt retained destination fails. |
| G7A-006 | `docs/ux-audit/2026-10-14-round3-reaudit/run_all.py` aggregates child and receipt failures, records missing receipts, distinguishes failed completion from passed and exits nonzero. Each invocation retains its records under a fresh `runs/native-*` directory; `run.py` receives that owned output path. Two-case fixture: exit 0 then exit 1, with both run records and original historical receipts preserved. Existing shell wrapper propagates status unchanged. |
| G7B-001 | `docs/ux-audit/2026-10-15-round4-reaudit/native_options_remaining.py` starts each family menu inventory empty. Existing OPTIONS screenshot/control rows no longer enter menus. |
| G7B-002 | `docs/ux-audit/2026-10-16-round5-reaudit/native_editor.py` and round-four `native_shell.py` select exactly one visible window using the spawned editor PID via xdotool, failing on missing/ambiguous results. Controlled command verifies PID 42, parses window 123 as 0x7b; parent global title command fails this ownership contract. Requires xdotool on historical X11 host. |
| G7B-003 | `docs/ux-audit/2026-10-16-round5/review1_bcg_source.py` reports recorded metadat package version. Injected different-version appears verbatim instead of invented 1.6-0. No actual BCG/R numerical rerun claimed. |
| G7B-004 | `docs/ux-audit/2026-10-16-round6-release-fixes/axis_text_probe.py` requires exact four-family/11-height filename set before checking all six tick values. All 44 synthetic cases pass; empty, substituted identity and wrong interior tick fail. Existing R generator and wrapper already produce those intended names, unchanged. |
| G7B-005 | Round-six `reviewer_preflight.py`, `REVIEWER-REPRODUCE.sh`, `reviewer_curate.py`: preflight historical before receipt, success status, log evidence path, passed native manifest, steps and existing captures before install/capture/curation writes. Missing receipt/capture fail; complete disposable fixture passes. Parent wrapper with uv command stand-in attempts install before preflight and fails ordering control. Historical bundle remains an explicit external prerequisite. |
| G7B-006 | Round-six `reviewer-gallery.html` uses relative paths; curator normalizes and validates local assets on reproduction. All 51 paths resolve after gallery asset relocation with identical SHA256 bytes. Removed curator deletion of two original frames. No images invented or changed. |

## Repeatable evidence

Run from this worktree, locked uv Python 3.11.9 on Windows:

```
$env:RCMS_QT6_RCC='C:/Users/Ali-Salman/Documents/Code/rc-metastudio/build/qt-rcc/6.11.1/msvc2022_64/bin/rcc.exe'
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
uv run python -c "from scripts.verify import run_typing; from pathlib import Path; run_typing(Path('build/qt6-verification'))"
uv run python artifacts/fixes/historical-01-contracts.py --baseline
uv run python artifacts/fixes/historical-01-contracts.py
```

Retained ignored evidence: `artifacts/fixes/historical-01/`. Failure modes were recorded before edits. The executable contracts were constructed after initial edits and executed against the preserved parent with `git show f6ffae40`, rather than a chronological test-first implementation. This is a process deviation, not a claim of chronological red/green. Final parent control: `baseline-final-02.log`, 12 intended failures, no errors. Current: `contracts-final-03.log`, 12 passed. Inputs and stand-ins are generated by the committed contract module; subprocesses only operate inside disposable fixtures. AST-selected executable historical blocks isolate unavailable Qt/R/X11 boundaries; they are contract proof, not native historical execution. Earlier failed fixture attempts are retained separately and are not qualification.

Strict typing preceded checks: win32 repository-wide command/transcript in `artifacts/verification/typing/20261107T181546-7d5eebea`; repeated successfully in `20261107T182103-c816d1fb`. The exact command includes generated form/module search paths and `src/rc_metastudio scripts tests r/RCMetaR/inst/qa`. Forms logs and both gate transcripts are retained in batch evidence. Changed Python syntax and `git diff --check` passed. Git Bash syntax check was run for the changed shell drivers.

## Limits

No GUI or actual historical R fit was run. No new persisted project/numerical output claim; only disposable receipt/archive/manifest/file outputs described above. Axis tick parser and OS commands are controlled stand-ins; actual R SVG/font rendering and X11 process properties remain native-host checks. Raster test exercises the historical acceptance branch with controlled comparison results, not a fresh Windows capture. SIGINT/SIGTERM cleanup is implemented but native signal/interruption, forced termination, power-loss and rollback-write-failure injection were not qualified; persistent recovery copies protect failed restore attempts, and uncatchable termination may require manual recovery. Reference runtime-04 was neither written nor used. Full-profile qualification belongs to the parent.

Batch hash manifest and exact tracked file list are retained as `artifacts/fixes/historical-01/hashes.json`; commit identity and final file list are retained in `commit.txt`. Worktree/evidence remain available. No push or PR.
