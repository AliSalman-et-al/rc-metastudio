# Windows frozen R probe investigation

Base: origin/master 7646d481. Target: Windows x64.

## Failure evidence

The four retained failing probes report R **4.6.2**, not the locked 4.6.1.
All have the same bundled R home, configured library, `.libPaths()`, rpy2 API
bridge path and CFFI mode. No user library appears. `probe.diff` compares run
41839989498's failed attempt 1 with its successful attempt 2 at the same commit:
the only JSON difference is R's observed version (4.6.2 versus 4.6.1).
The diagnostics artifact survives reruns; the passing probe must be extracted
from the successful package ZIP rather than that old diagnostics artifact.

Runs: 41839989498 (PR 558), 41953107031 (PR 564), 41955030513
(job 127007914848, PR 565), 41955480808 (job 127009563262, PR 565,
925e35a). JSON files here preserve all four failing observations.

Download commands (run from repository root):

```
gh run download 41839989498 -n RCMetaStudio-0.5.1-windows-x64-diagnostics -D /tmp/probe-flake/pass
gh run download 41839989498 -n RCMetaStudio-0.5.1-windows-x64 -D /tmp/probe-flake/pass-package
gh run download 41953107031 -n RCMetaStudio-0.5.1-windows-x64-diagnostics -D /tmp/probe-flake/fail564
gh run download 41955030513 -n RCMetaStudio-0.5.1-windows-x64-diagnostics -D /tmp/probe-flake/fail
gh run download 41955480808 -n RCMetaStudio-0.5.1-windows-x64-diagnostics -D /tmp/probe-flake/fail-fourth
gh run view 41839989498 --attempt 1 --log-failed
gh run view 41955030513 --log-failed
```

The successful ZIP contains both `R/bin/x64/R.dll` and `_internal/R.dll`,
and both `R/bin/x64/Rblas.dll` and `_internal/Rblas.dll` (ZIP member paths
use backslashes). PyInstaller's dependency collection supplies the second copy.
The wrapper restored the ambient R_HOME after building rpy2, before Analysis,
and did not bind Analysis's PATH to staged R. Thus the runtime loaded through
the collected API bridge can differ from the runtime selected by R_HOME.
The old probe's shared_library_path is constructed from configured R_HOME;
it does not independently identify the DLL loaded by Windows. The live R
version exposes the mismatch despite that configured path.

## Fix and qualification

Keep Analysis on staged R via R_HOME and PATH; restore both afterward.
Remove collected R.dll/Rblas.dll/Rlapack.dll so only the explicitly staged
runtime owns those DLLs. Preserve the fail-closed inspector and version pin.
No retries or inspection exceptions.

Planned behavioral proof: three independent manual dispatches of
`gh workflow run fast-verification.yml --ref fix/ci-package-probe-flake`,
including staged and extracted package qualification. These exercise the actual
frozen executable rather than a mocked DLL loader.

Local commands, Linux host targeting win32 for strict typing:

```
uv sync --locked
uv pip install pefile
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
uv run python -c 'from scripts.verify import run_typing; from pathlib import Path; run_typing(Path("build/qt6-verification"))'
RCMS_QT6_BUILD_ROOT="$PWD/build/qt6-verification" uv run python -m pytest tests/packaging/contract -q
```

Strict typing passed; packaging contracts: 73 passed, 8 skipped (platform gates).
Initial typing lacked the Windows inspection dependency pefile; installed it
and repeated the gate. Initial contract invocation lacked the generated UI root;
repeated with RCMS_QT6_BUILD_ROOT as shown. No GUI qualification claimed locally.

## CI results

1. https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/41956186577
   — entire workflow green, including required Windows package qualification.
   Head 9d1b1fccfd8ecc07e29f90480a4288bee0acf598.
2. https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/41958102505
   — entire workflow green, including required Windows package qualification.
   Same executable source; intervening commit contains investigation evidence only.

`ci1-probe.json` comes from the first fixed package ZIP. It reports R 4.6.1.
Its ZIP has only `R/bin/x64/{R.dll,Rblas.dll,Rlapack.dll}` and no `_internal`
copies. `ci1-result.json` and `ci2-result.json` retain job conclusions and links.
The third manual dispatch and its result will be linked in the PR, avoiding
another documentation-only head change after qualification.
