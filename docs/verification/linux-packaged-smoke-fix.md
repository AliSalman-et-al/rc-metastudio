# Linux packaged startup and runtime HOME

Frozen startup must configure the bundled R environment before
`settings.setup_directories()`. Configuration replaces HOME with a private
runtime home. Creating Qt's application-data base first can leave the later
R working-directory reset pointing at a directory that was never created.
R itself still loads through the deferred timer after the shell is visible.

Preserve this ordering when changing bootstrap. Reproduce with a fresh HOME,
no XDG_DATA_HOME, the actual frozen executable, German locale and fractional
scales 1.25/1.50/1.75. Require bounded exit, a native xcb surface record and
accepted close. Retain exact child commands, environment, runtime identity,
stdout/stderr, timeout outcome and surface JSON. A source probe cannot qualify
an extracted GitHub archive, signing, another platform or newly assembled bytes.

Run the strict typing gate before GUI qualification, then the affected
packaging and runtime checks:

```powershell
uv run python -m pytest tests/packaging/contract/test_linux_distributable_contract.py tests/python/fast/test_r_runtime.py -q
```

Build and qualify the actual Linux artifact using the
[maintaining guide](../maintaining.md#build-the-linux-package) and
[release process](../release.md). Historical local rebuild results and their
machine-specific helper scripts remain in Git; they are not current release
evidence.
