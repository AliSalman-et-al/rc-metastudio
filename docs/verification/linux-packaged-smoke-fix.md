# Linux packaged startup HOME ordering

Proof planned before implementation (release source 934e19119694d8927e620000d4ceee08c0581bd5):

- In a child process with a fresh HOME and no XDG_DATA_HOME, create the ordinary Qt application-data directory, then apply frozen runtime directory configuration. Observe that Qt's new AppDataLocation differs and does not exist. This reproduces the setwd precondition without fabricating an R backend.
- Run the actual Linux frozen executable with fresh HOME, no XDG_DATA_HOME, German package locale and scale 1.25, bounded externally. Before the fix it must fail to exit/write a surface record; after the fix it must exit zero, report the native xcb surface and accepted close. Repeat at 1.50 and 1.75.
- Run repository-wide strict typing before GUI qualification, retaining target and transcript, and affected packaging contracts. A source or locally rebuilt executable is not qualification of the failed GitHub archive.

Failure mechanism: settings.setup_directories creates Qt's HOME-derived base before the deferred R loader calls configure_bundled_r_environment. Frozen bootstrap replaces HOME with a private runtime home. reset_r_working_directory then recomputes Qt's base under that new home, where no directory was created. The R exception enters the interactive backend-error dialog inside processEvents, so the automation readiness check never returns.

## Implementation and observed verification

The frozen composition now configures its bundled R environment before
`settings.setup_directories()`. R itself still loads through the deferred timer
after the shell is visible. Configuration is already idempotent; no alternate
working-directory policy or timeout increase is needed.

Evidence is retained in `artifacts/verification/linux-smoke-fix/` in the dedicated
`linux-packaged-smoke` worktree. `prove-home-change.py` and
`home-change-before.json` retain the real Qt directory-change reproduction.
`drive.py` retains the fresh-HOME frozen-process drive, exact child commands,
environment, timeout, native surface JSON and process results for every scale.
`build.sh` retains the PyInstaller command and environment.

Commands (run from the dedicated worktree):

```sh
uv sync --locked
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
uv run python artifacts/verification/linux-smoke-fix/prove-home-change.py
uv pip install pefile
uv run --no-sync ty check --python-platform win32 \
  --extra-search-path build/qt6-verification/generated/rc_metastudio \
  --extra-search-path build/qt6-verification/generated/rc_metastudio/forms \
  --extra-search-path . --extra-search-path src/rc_metastudio \
  --extra-search-path src --extra-search-path scripts \
  --extra-search-path tests/python/gui \
  src/rc_metastudio scripts tests r/RCMetaR/inst/qa
uv run --no-sync python -m pytest tests/packaging/contract/test_linux_distributable_contract.py tests/python/fast/test_r_runtime.py -q
RCMS_QT6_BUILD_ROOT="$PWD/build/qt6-verification" uv run --no-sync python -m pytest tests/packaging/contract -q
bash artifacts/verification/linux-smoke-fix/build.sh
.venv/bin/python artifacts/verification/linux-smoke-fix/drive.py after "$PWD/build/linux-fix/dist/LaunchRCMetaStudio.sh"
git diff --check
```

Results: strict typing passed with the documented win32 target; focused contracts
7 passed; complete packaging contracts 72 passed, 8 skipped. The initial Linux
Ty target reported 12 existing platform/import diagnostics (winreg and missing
pefile); the documented win32 target and installation of pefile resolved them.
An initial complete-contract invocation omitted RCMS_QT6_BUILD_ROOT and failed
one form-import check; the configured invocation passed.

Native Linux Mint 22.3 (Ubuntu Noble base), real private R 4.6.1, Qt xcb,
German locale, scales 1.25/1.50/1.75: all exited zero within the 30-second bound,
wrote the requested surface JSON, and accepted close with no visible window.
The standalone PyInstaller build initially lacked the cursor library that the
full packaging script supplies; copying the existing packaged libxcb-cursor.so.0
resolved that startup dependency. The pinned rpy2-rinterface 3.6.6 API extension
was copied from the existing development environment (hash retained); an attempted
source rebuild failed on missing system linker development libraries. The
launcher and private R tree were reused from the existing local extracted
package; the rebuilt executable contains the changed source. These checks do
not qualify a newly assembled release archive or Windows/macOS runtime behavior.
No release workflow was dispatched.
