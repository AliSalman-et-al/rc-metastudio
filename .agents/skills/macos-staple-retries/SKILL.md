---
name: macos-staple-retries
description: Check the trusted macOS finalizer when changing staple validation, retry classification, backoff, or publication order.
---

# macOS staple retries

After Apple accepts the saved submission, finalize its exact DMG. Retry CloudKit connection loss or timeout within three attempts. A permanent error or exhausted budget must stop before signature verification and preserve both the signed input and any existing qualified output.

From the repository root, use the locked verification environment and Bash.

```powershell
uv run pytest tests/packaging/contract/test_macos_staple_retry_model.py -q
```

The model enumerates every terminal trace over six outcome classes and three attempts. It runs the real `finalize` branch of `scripts/sign-notarize-macos-artifact.sh` for each trace and observes the order of Apple commands, delays and entry into signature verification. It checks exact input and prior output bytes and retention of Apple messages. The Windows quick lane and the focused macOS packaging lane both run it. Bash, Python and filesystem operations are real. Apple responses and delays are controlled. The model stops at signature verification and covers one finalization process. Mounted runtime and publication checks belong to package qualification.

Replay the CloudKit failure fixed by [#586](https://github.com/AliSalman-et-al/rc-metastudio/pull/586) against the actual pre-fix script.

```powershell
$env:RELEASE_PROOF_REVISION = 'be1fa7275b42527c0447711f333f9b4b3b143e5f'
uv run pytest 'tests/packaging/contract/test_macos_staple_retry_model.py::test_staple_retry_model[connection-lost-valid]' -q
Remove-Item Env:RELEASE_PROOF_REVISION
```

The old finalizer waits for Apple, staples the DMG, sees the first validation return exit 68 with `NSURLErrorDomain Code=-1005`, and stops. The current finalizer waits 15 seconds, validates again, and reaches signature verification. Use `--basetemp` with a disposable path to retain the script, inputs, traces and transcripts. A failure before the first validation indicates a fixture or environment problem. Compare `trace.log` with the expected first divergent event before changing the model.

The model was checked against `scripts/sign-notarize-macos-artifact.sh` at `cc2472684a59f87a30ec7a73382b73a0fecc27c3`. When the finalizer changes, confirm the model still describes the accepted-submission path and its retry policy, replay #586, and update the sync revision.
