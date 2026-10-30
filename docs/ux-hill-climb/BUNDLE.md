# Linux bundle audit

Baseline source: 6a2af139 (application unchanged from 176c88b5). Host Linux Mint 22.3, Noble base, x86_64, glibc 2.39. Installer remains the portable tar.gz. Windows ZIP and macOS packaging are separate host lanes and are not rebuilt here.

## Build and measurement

Release entry point: `bash scripts/package-linux.sh` installs locked Python and invokes `bash scripts/build-linux-package.sh --python-exe "$PWD/.venv/bin/python"`. The latter installs pinned R/authority packages, generates Qt, runs packaging/pyinstaller/rc-metastudio-linux.spec, stages runtime/samples/notices, archives and qualifies the extracted executable. Windows and macOS have corresponding build scripts/specs. pyproject.toml package data includes forms, images and project schemas, not docs/artifacts.

Exact build command for both audit runs:

```sh
bash scripts/build-linux-package.sh --python-exe "$PWD/.venv/bin/python"
```

Initial retained staging directory: `build/linux-package/work/archive-staging/RCMetaStudio-linux-x64` (September output; not claimed as current-source build). Logical file bytes, following file symlinks, measured with Python pathlib rglob/stat; filesystem allocation and compressed archive bytes differ. No archive existed in artifacts at audit start. Measurement inventory saved to build/bundle-audit/before.json before invoking the build, which replaces its own work directory.

```python
from pathlib import Path
from collections import Counter
p = Path("build/linux-package/work/archive-staging/RCMetaStudio-linux-x64")
files = {str(f.relative_to(p)): f.stat().st_size
         for f in p.rglob("*") if f.is_file()}
totals = Counter()
for path, size in files.items():
    totals[path.split("/")[0]] += size
print(sum(files.values()), totals)
print(sorted(files.items(), key=lambda x: x[1], reverse=True)[:15])
```

Initial retained output: **704,078,995 bytes**.

| Top-level path | Logical bytes |
| --- | ---: |
| RCMetaStudio | 395,082,198 |
| R | 308,765,449 |
| third-party-notices | 154,426 |
| sample_projects | 37,194 |
| LICENSE | 35,150 |
| qualification | 2,487 |
| NOTICE.md | 1,584 |
| LaunchRCMetaStudio.sh | 507 |

| Largest file | Bytes |
| --- | ---: |
| RCMetaStudio/_internal/libicudata.so.73 | 32,035,888 |
| RCMetaStudio/_internal/PyQt6/Qt6/lib/libicudata.so.73 | 32,035,888 |
| RCMetaStudio/_internal/libicudata.so.74 | 30,795,392 |
| RCMetaStudio/_internal/libpython3.11.so.1.0 | 26,820,680 |
| RCMetaStudio/_internal/libscipy_openblas64_-32a4b2a6.so | 25,409,073 |
| RCMetaStudio/_internal/numpy.libs/libscipy_openblas64_-32a4b2a6.so | 25,409,073 |
| R/lib/libR.so | 13,720,256 |
| RCMetaStudio/_internal/libQt6Gui.so.6 | 11,511,024 |
| RCMetaStudio/_internal/PyQt6/Qt6/lib/libQt6Gui.so.6 | 11,511,024 |
| RCMetaStudio/_internal/numpy/_core/_multiarray_umath.cpython-311-x86_64-linux-gnu.so | 10,407,681 |
| RCMetaStudio/_internal/libgtk-3.so.0 | 8,156,632 |
| RCMetaStudio/_internal/libQt6Widgets.so.6 | 8,155,496 |
| RCMetaStudio/_internal/PyQt6/Qt6/lib/libQt6Widgets.so.6 | 8,155,496 |
| R/library/Matrix/libs/Matrix.so | 7,567,464 |
| RCMetaStudio/_internal/libQt6Core.so.6 | 7,565,608 |

## Runtime boundary and proof obligations

Before editing packaging inputs: prove runtime starts from extracted archive, R/Qt runtime probe succeeds, samples remain loadable and notices/schemas remain. Compare complete path/byte inventories before/after. Development-only qualification observations must stay outside shipped tree. Source docs/artifacts and referenced source files must remain untouched. Do not remove duplicate-looking shared libraries without dependency/relocation proof.

Samples are runtime inputs: settings.get_sample_projects_path and main_window sample-path resolution use this directory. Keep .rcms examples, README and manifest/source provenance. R package help/resources are not presumed disposable. Existing PyInstaller datas are explicit and do not sweep repository evidence/cache/test directories into the app.

Current-source baseline build and subsequent cleanup results are recorded below when available. Logs live under build/bundle-audit; no pass is inferred from the old staging directory.
