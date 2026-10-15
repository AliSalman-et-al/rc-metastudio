# Native re-audit replay

Use the audited application source at `ddeef0a` or the audit-only descendants on `ux/audit-improvements`. Read the repository verification skill first. Run from the repository root on a visible Linux X11 desktop. The retained test-owned R library must still exist and match [PROVENANCE](PROVENANCE.json); do not install over a user library.

```bash
source docs/ux-audit/2026-10-14-round3/ENV.sh
export DISPLAY=:0
uv run python scripts/verify_rcms.py doctor --native
```

[OUTCOMES](OUTCOMES.json) contains the exact command, environment, source revision, exit status, elapsed time and transcript hash for every completed recorder run. Native helper entries also bind manifest hashes and verify every retained artifact. Failed runs and interruptions are preserved in [FAILURES](FAILURES.json). Raw logs and test-owned inputs remain ignored, rather than being mistaken for curated screenshots.

The root `native_*.py` scripts are audit drivers, not application changes. The additional driver sources are embedded verbatim in [REPLAY-SOURCES](REPLAY-SOURCES.json), including their hashes. Restore them at their recorded relative locations:

```bash
python3 - <<'PYCODE'
from pathlib import Path
import hashlib,json
p=Path('docs/ux-audit/2026-10-16-round5-reaudit')
for item in json.loads((p/'REPLAY-SOURCES.json').read_text()):
    data=item['source'].encode()
    assert hashlib.sha256(data).hexdigest()==item['sha256']
    target=p/item['path']
    target.parent.mkdir(parents=True,exist_ok=True)
    assert not target.exists() or target.read_bytes()==data, target
    target.write_bytes(data)
PYCODE
```

Use a fresh checkout or archive previous owned raw run directories before replay. `native_design.py` deliberately refuses to overwrite an existing project fixture directory. Run native GUI commands **serially**. The historical queue records the interrupted run/recovery chronology; it is not a clean-checkout entry point because its first stage waits for a prior matrix receipt.

For the 50-cell matrix, run each of these families through the recorder and `native_matrix.py`: `onearm-proportion`, `onearm-mean`, `reg-coef`, `generic-effect`, `twoarm-proportion`, `twoarm-mean`, `twoarm-smd`, `diagnostic`, `hr`, `irr`. Example:

```bash
uv run python docs/ux-audit/2026-10-16-round5-reaudit/run.py matrix-hr \
 uv run python scripts/run_with_timeout.py --timeout-seconds 600 --label 'native matrix hr' -- \
 uv run python docs/ux-audit/2026-10-16-round5-reaudit/native_matrix.py hr
```

Each family writes actual input projects, exact analysis parameter/observation steps, display SVGs, text reports, native screenshots and an index. [MATRIX](MATRIX.md) links the 50 curated figure/report pairs. Figure/report agreement is recorded in [INSPECTIONS](INSPECTIONS.json); numerical authority comparisons are a separate 91-case run in [AUTHORITIES](AUTHORITIES.json).

Run `native_design.py` before `native_shell.py` because the shell editor proof opens the report exported by the design drive. Then run `native_options.py`, `native_editor.py` (includes the remaining diagnostic/HR/IRR option inventory), `native_extra.py`, restored `raw/native_samples.py`, and `raw/native_guard_keyboard.py` using the exact completed commands in OUTCOMES. The sample wrapper uses owned copies and checks original archive bytes after save/reopen. For long names, run restored `raw/native_long_names.py twoarm-proportion` separately with `RCMS_AUDIT_STYLE=default`, `revman` and `bmj`.

The complete maintained native scenario registry is discoverable from `SCENARIOS` in `scripts/verify_rcms.py`; run each as `uv run python scripts/verify_rcms.py SCENARIO --native`. The feature map describes each scenario's assertions and entry-point limits. Repeat `review1-design --native` with `QT_SCALE_FACTOR=1.25`, `1.5` and `2.0`. These are Qt scaling checks on this host, not OS or screen-reader qualification. Inspect every image before citing it; passing a render assertion does not establish layout quality.

The targeted `raw/native_metric_menu.py` traverses only currently attached menus and reproduces R5-09. The final self-contained `raw/native_tiny_raw_keyboard_replay.py` enters the valid tiny SD through an editable delegate, captures/acknowledges its own warning, saves/reopens an owned copy and records actual values. **Its exit 0 denotes completed observation; `stored_sd_preserved:false` is the high-severity defect.** Do not replay historical XIDs from the first manually acknowledged probe. The first double-click attempt and earlier F10/Home driver variants are retained for failure provenance.

`raw/native_startup_settled.py` calls the real startup routine and observes native Qt/EWMH states until stable for 200 ms (bounded 5 s); it sends no extra maximize command. It is separate evidence, not a passing replacement for the two failed unmodified `project-shell` invocations. The normal/fullscreen transitions settled within 296 ms including the stability floor. Other shell/guard transactions have independent native replays.

All 112 registered non-doctor scenarios were attempted;111 have passing fresh native receipts. The remaining failed maintained scenario is `project-shell`. The full native helper registry's ordinary-value checks do not qualify arbitrary numeric input magnitudes; the tiny-SD probe deliberately demonstrates that distinction.
