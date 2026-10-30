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

## Current-source baseline and packaging edit

The first build failed compiling rpy2: missing linker names `-ldeflate`, `-lzstd`, `-ltirpc`. Runtime libraries were already installed. Created only task-owned symlinks in build/bundle-audit/linker to /lib/x86_64-linux-gnu/libdeflate.so.0, libzstd.so.1 and libtirpc.so.3 (named libdeflate.so, libzstd.so, libtirpc.so). No system installation or statistical package change.

Both successful-baseline and cleanup builds use this same command/environment:

```sh
LIBRARY_PATH="$PWD/build/bundle-audit/linker" bash scripts/build-linux-package.sh --python-exe "$PWD/.venv/bin/python"
```

Baseline exited 0, including native Xvfb extracted-package qualification. Current-source logical total: **703,575,404 bytes**, archive **302,724,316 bytes**. Top-level bytes: RCMetaStudio 394,446,019; R 308,871,461; sample_projects 63,770; third-party-notices 154,426; LICENSE 35,150; qualification 2,487; NOTICE.md 1,584; launcher 507. Complete SHA-256/path/byte inventory: build/bundle-audit/current-before.json, generated by build/bundle-audit/inventory.py using the measurement above plus file SHA-256 and archive stat. Baseline logs: baseline-build.log (failed), baseline-build-retry.log (passed). Qualification JSON copied to build/bundle-audit/baseline-evidence before rebuilding.

Packaging edit: runtime-probe.json now goes directly to work/qualification, outside archive-root. Remove only installed R package `tests` and `demo` directories at depth two in the **staged copy** of R/library. Neither installed build runtime nor source packages are pruned. Application Python/R code contains no calls loading these directories; real extracted-package qualification remains mandatory. Keep help/doc/data, sample projects/provenance, schemas, licenses and libraries. Repository docs/artifacts are not packaging inputs and are not deleted. Windows/macOS qualification payload has host-specific provenance/reinspection dependencies; those lanes are unchanged and unverified here.

Full path inspection additionally identified package testdata/tinytest suites and RCMetaR/qa (visual qualification scripts including __pycache__). The first cleanup rebuild was deliberately stopped during dependency metadata validation (owned R process SIGTERM, exit 143), before producing an archive. Extended the same staged-copy exclusion to testdata/tinytest and specifically RCMetaR/qa, then restarted the identical build command. These paths have no application Python/R references. No source QA scripts or evidence were deleted.
