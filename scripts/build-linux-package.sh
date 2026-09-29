#!/usr/bin/env bash
set -euo pipefail

python_exe=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --python-exe)
      python_exe="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
artifact_name="RCMetaStudio-linux-x64"
artifact_dir="$repo_root/artifacts"
artifact_path="$artifact_dir/$artifact_name.tar.gz"
evidence_path="$artifact_dir/$artifact_name-evidence.json"
build_root="$repo_root/build/linux-package"
work_root="$build_root/work"
dist_root="$build_root/dist"
archive_root="$work_root/archive-root/$artifact_name"
qualification_root="$work_root/qualification"
r_deb_name="r-4.6.1_1_amd64.deb"
r_deb_url="https://cdn.posit.co/r/ubuntu-2404/pkgs/$r_deb_name"
r_deb_sha256="5af816371126c8e5895600de035153cd3a64b12f4beb43f291ee34bf24f8fd2d"
cursor_deb_name="libxcb-cursor0_0.1.4-1build1_amd64.deb"
cursor_deb_url="https://archive.ubuntu.com/ubuntu/pool/universe/x/xcb-util-cursor/$cursor_deb_name"
cursor_deb_expected_sha256="137cf52479b5a9d8c5926d70d311af04be41941a32ee777340d704cc458c06d8"
cursor_deb_sha256=""
cursor_source=""
cran_repo="https://packagemanager.posit.co/cran/2026-07-16"
linux_cran_repo="https://packagemanager.posit.co/cran/__linux__/noble/2026-07-16"
r_home="$work_root/r-home"
r_library="$r_home/library"
ppm_archives="$qualification_root/ppm-archives"
runtime_probe="$archive_root/qualification/runtime-probe.json"
smoke_evidence="$qualification_root/packaged-smoke.json"
smoke_log="$qualification_root/packaged-smoke.log"
worker_evidence="$qualification_root/worker-journey.json"
runtime_probe_stdout="$qualification_root/runtime-probe.stdout.log"
runtime_probe_stderr="$qualification_root/runtime-probe.stderr.log"

step() {
  printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$1"
}

die() {
  echo "$1" >&2
  exit 1
}

if [ "$(uname -s)" != "Linux" ] || [ "$(uname -m)" != "x86_64" ]; then
  die "Linux packaging requires an x86_64 host."
fi
if [ ! -r /etc/os-release ]; then
  die "Linux packaging requires Ubuntu 24.04 (Noble)."
fi
. /etc/os-release
if { [ "${ID:-}" != "ubuntu" ] || [ "${VERSION_ID:-}" != "24.04" ]; } &&
   [ "${UBUNTU_CODENAME:-}" != "noble" ]; then
  die "Linux packaging requires Ubuntu 24.04 (Noble) or a Noble-based distribution."
fi
host_glibc="$(getconf GNU_LIBC_VERSION | awk '{print $2}')"
if [ "$host_glibc" != "2.39" ]; then
  die "Linux packaging requires glibc 2.39 to preserve the Ubuntu 24.04 baseline; found $host_glibc."
fi
if [ -z "$python_exe" ]; then
  python_exe="$repo_root/.venv/bin/python"
fi
[ -x "$python_exe" ] || die "Python environment was not found at $python_exe. Run scripts/package-linux.sh."
command -v dpkg-deb >/dev/null 2>&1 || die "Linux packaging requires dpkg-deb."
command -v curl >/dev/null 2>&1 || die "Linux packaging requires curl."
command -v xvfb-run >/dev/null 2>&1 || die "Linux packaging requires xvfb-run for native Qt qualification."

cd "$repo_root"
mkdir -p "$artifact_dir/download-cache/linux-x64" "$qualification_root"
rm -rf "$work_root" "$dist_root"
mkdir -p "$work_root" "$dist_root" "$qualification_root" "$artifact_dir/download-cache/linux-x64"
rm -f "$artifact_path" "$artifact_path.tmp" "$evidence_path"

download_pinned() {
  local name="$1" url="$2" expected="$3" path="$artifact_dir/download-cache/linux-x64/$1"
  if [ ! -f "$path" ] || [ "$(sha256sum "$path" | awk '{print $1}')" != "$expected" ]; then
    rm -f "$path" "$path.partial"
    step "Downloading pinned $name" >&2
    curl --fail --location --proto '=https' --tlsv1.2 --retry 3 "$url" --output "$path.partial"
    [ "$(sha256sum "$path.partial" | awk '{print $1}')" = "$expected" ] || die "SHA-256 mismatch for $name."
    mv "$path.partial" "$path"
  fi
  [ "$(sha256sum "$path" | awk '{print $1}')" = "$expected" ] || die "Cached $name failed SHA-256 verification."
  printf '%s\n' "$path"
}

r_deb="$(download_pinned "$r_deb_name" "$r_deb_url" "$r_deb_sha256")"
mkdir -p "$work_root/r-extract"
dpkg-deb -x "$r_deb" "$work_root/r-extract"
cp -a "$work_root/r-extract/opt/R/4.6.1/lib/R" "$r_home"
[ -x "$r_home/bin/exec/R" ] || die "Pinned R archive does not contain the expected R 4.6.1 runtime."

step "Making Posit R launchers relocatable"
"$python_exe" - "$r_home" <<'PY'
from pathlib import Path
import sys

home = Path(sys.argv[1]).resolve()
launcher = home / "bin" / "R"
text = launcher.read_text(encoding="utf-8")
marker = "R_HOME_DIR=\"/opt/R/4.6.1/lib/R\""
if marker not in text:
    raise SystemExit("unexpected Posit R launcher; cannot make it relocatable")
tail = text[text.index("usage=\"") :]
header = '''#!/bin/bash
# Relocatable wrapper for the private R runtime.
r_script_dir=${0%/*}
R_HOME_DIR="$(CDPATH= cd -- "$r_script_dir/.." && pwd)"
if test -n "${R_HOME}" && test "${R_HOME}" != "${R_HOME_DIR}"; then
  echo "WARNING: ignoring environment value of R_HOME" >&2
fi
R_HOME="${R_HOME_DIR}"
export R_HOME
R_SHARE_DIR="${R_HOME}/share"
export R_SHARE_DIR
R_INCLUDE_DIR="${R_HOME}/include"
export R_INCLUDE_DIR
R_DOC_DIR="${R_HOME}/doc"
export R_DOC_DIR

'''
launcher.write_text(header + tail, encoding="utf-8")
launcher.chmod(0o755)

rscript = home / "bin" / "Rscript"
rscript.write_text('''#!/bin/sh
r_script_dir=${0%/*}
R_HOME="$(CDPATH= cd -- "$r_script_dir/.." && pwd)"
export R_HOME
export R_SHARE_DIR="$R_HOME/share"
export R_INCLUDE_DIR="$R_HOME/include"
export R_DOC_DIR="$R_HOME/doc"
if [ "$#" -gt 0 ] && [ "${1#-}" = "$1" ]; then
  script="$1"
  shift
  exec "$R_HOME/bin/R" --no-save --no-restore --no-echo "--file=$script" --args "$@"
fi
exec "$R_HOME/bin/R" --no-save --no-restore --no-echo "$@"
''', encoding="utf-8")
rscript.chmod(0o755)
PY

step "Checking the relocated private R runtime"
R_HOME="$r_home" LD_LIBRARY_PATH="$r_home/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
  "$r_home/bin/Rscript" -e 'stopifnot(as.character(getRversion()) == "4.6.1", normalizePath(R.home()) == normalizePath(Sys.getenv("R_HOME")))'

step "Building the locked rpy2 API bridge against private R"
R_HOME="$r_home" \
R_LIBS="$r_library" \
R_LIBS_USER="$r_library" \
LD_LIBRARY_PATH="$r_home/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
PATH="$r_home/bin:$PATH" \
RPY2_CFFI_MODE=API \
uv pip install --python "$python_exe" --no-cache --no-deps --reinstall --no-binary rpy2-rinterface "rpy2-rinterface==3.6.6"
R_HOME="$r_home" \
LD_LIBRARY_PATH="$r_home/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
RPY2_CFFI_MODE=API \
"$python_exe" -c 'import rpy2.robjects; from rpy2.rinterface_lib import openrlib; print(openrlib.R_HOME)' | grep -F "$r_home" >/dev/null \
  || die "rpy2 API bridge did not initialize the private R runtime."

step "Installing the dated Ubuntu 24.04 R binary closure"
R_HOME="$r_home" \
R_LIBS="$r_library" \
R_LIBS_USER="$r_library" \
RCMS_R_LIBS="$r_library" \
RCMS_CRAN_REPO="$cran_repo" \
RCMS_POLICY_PYTHON="$python_exe" \
LD_LIBRARY_PATH="$r_home/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
PATH="$r_home/bin:$PATH" \
"$r_home/bin/Rscript" "$repo_root/scripts/install-r-deps-linux.R" \
  "$repo_root" "$r_library" "$ppm_archives" 2>&1 | tee "$qualification_root/install-r-deps.log"

step "Installing and checking the local RCMetaR authority package"
R_HOME="$r_home" \
R_LIBS="$r_library" \
R_LIBS_USER="$r_library" \
LD_LIBRARY_PATH="$r_home/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
PATH="$r_home/bin:$PATH" \
"$r_home/bin/R" CMD INSTALL --library="$r_library" "$repo_root/r/RCMetaR" \
  2>&1 | tee "$qualification_root/install-rcmetar.log"
R_HOME="$r_home" R_LIBS="$r_library" R_LIBS_USER="$r_library" \
LD_LIBRARY_PATH="$r_home/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
  "$r_home/bin/Rscript" -e 'lib <- normalizePath(Sys.getenv("R_LIBS_USER")); .libPaths(c(lib, .libPaths())); pkgs <- c("mada", "metafor", "meta", "rsvg", "svglite", "tiff", "xml2", "RCMetaR"); stopifnot(all(vapply(pkgs, requireNamespace, logical(1), quietly = TRUE))); version <- function(package) utils::packageDescription(package, fields = "Version", lib.loc = lib); stopifnot(version("mada") == "0.5.12", version("meta") == "8.5-0", version("RCMetaR") == "0.4.1")'

step "Generating Qt resources and compiling the Linux desktop bundle"
qt6_build_root="$work_root/qt6"
"$python_exe" "$repo_root/scripts/build_qt6.py" generate --build-root "$qt6_build_root"
export RCMS_QT6_BUILD_ROOT="$qt6_build_root"
export RCMS_R_HOME="$r_home"
export R_HOME="$r_home"
export R_LIBS="$r_library"
export R_LIBS_USER="$r_library"
export LD_LIBRARY_PATH="$r_home/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export RPY2_CFFI_MODE=API
export RCMS_PYQT_ROOT="$($python_exe -c 'from pathlib import Path; import PyQt6; print(Path(PyQt6.__file__).resolve().parent)')"
"$python_exe" -m PyInstaller --noconfirm --clean \
  --workpath "$work_root/pyinstaller-work" \
  --distpath "$dist_root" \
  "$repo_root/packaging/pyinstaller/rc-metastudio-linux.spec"

app_root="$dist_root/RCMetaStudio"
[ -x "$app_root/RCMetaStudio" ] || die "PyInstaller did not create the Linux application executable."
mkdir -p "$archive_root/qualification"
cp -a "$app_root" "$archive_root/RCMetaStudio"
cp -a "$r_home" "$archive_root/R"
cp -a "$repo_root/sample_projects" "$archive_root/sample_projects"
cp "$repo_root/LICENSE" "$repo_root/NOTICE.md" "$archive_root/"

cursor_library="$(ldconfig -p 2>/dev/null | awk '/libxcb-cursor\.so\.0 / {print $NF; exit}')"
if [ -z "$cursor_library" ]; then
  cursor_deb="$(download_pinned "$cursor_deb_name" "$cursor_deb_url" "$cursor_deb_expected_sha256")"
  cursor_deb_sha256="$cursor_deb_expected_sha256"
  cursor_source="pinned-deb"
  mkdir -p "$work_root/cursor-extract"
  dpkg-deb -x "$cursor_deb" "$work_root/cursor-extract"
  cursor_library="$work_root/cursor-extract/usr/lib/x86_64-linux-gnu/libxcb-cursor.so.0"
fi
[ -f "$cursor_library" ] || die "Missing libxcb-cursor.so.0; install Ubuntu package libxcb-cursor0 to build the Linux package."
if [ "$cursor_source" != "pinned-deb" ]; then
  cursor_owner="$(dpkg-query -S "$(readlink -f "$cursor_library")" 2>/dev/null | head -1 | cut -d: -f1)"
  [ -n "$cursor_owner" ] || die "Could not identify the Debian package owning $cursor_library."
  cursor_source="installed-package:$cursor_owner"
  cursor_notice="/usr/share/doc/$cursor_owner/copyright"
else
  cursor_notice="$work_root/cursor-extract/usr/share/doc/libxcb-cursor0/copyright"
fi
cursor_bundle_path="$archive_root/RCMetaStudio/_internal/libxcb-cursor.so.0"
cp -L "$cursor_library" "$cursor_bundle_path"
cursor_library_sha256="$(sha256sum "$cursor_bundle_path" | awk '{print $1}')"
mkdir -p "$archive_root/third-party-notices/linux-runtime"
[ -f "$cursor_notice" ] || die "Missing copyright notice for bundled libxcb-cursor0."
cp "$cursor_notice" "$archive_root/third-party-notices/linux-runtime/libxcb-cursor.so.0.copyright"

step "Bundling Noble R runtime shared libraries"
runtime_notice_root="$archive_root/third-party-notices/linux-runtime"
runtime_libraries=(libblas.so.3 liblapack.so.3 libgfortran.so.5 libgomp.so.1 libtk8.6.so)
{
  printf '# Bundled Linux runtime libraries\n\n'
  printf 'These Noble shared libraries are included for the private R runtime:\n\n'
  for soname in "${runtime_libraries[@]}"; do
    library_path="$(ldconfig -p 2>/dev/null | awk -v name="$soname" '$1 == name { print $NF; exit }')"
    [ -n "$library_path" ] && [ -f "$library_path" ] || die "Missing $soname; install its Ubuntu 24.04 runtime package."
    resolved_library="$(readlink -f "$library_path")"
    owner="$(dpkg-query -S "$resolved_library" 2>/dev/null | head -1 | cut -d: -f1)"
    [ -n "$owner" ] || die "Could not identify the Debian package owning $resolved_library."
    notice="/usr/share/doc/$owner/copyright"
    [ -f "$notice" ] || die "Missing copyright notice for Debian package $owner."
    cp -L "$library_path" "$archive_root/RCMetaStudio/_internal/$soname"
    cp "$notice" "$runtime_notice_root/$soname.copyright"
    package_version="$(dpkg-query -W -f='${Version}' "$owner")"
    library_sha256="$(sha256sum "$archive_root/RCMetaStudio/_internal/$soname" | awk '{print $1}')"
    printf -- '- `%s` from Debian package `%s` version `%s` (SHA-256 `%s`). License text: `%s.copyright`.\n' \
      "$soname" "$owner" "$package_version" "$library_sha256" "$soname"
  done
} > "$runtime_notice_root/README.md"

matrix_library="$archive_root/R/library/Matrix/libs/Matrix.so"
[ -f "$matrix_library" ] || die "Private R library is missing Matrix.so."
check_bundled_dependency() {
  local binary="$1" soname="$2" resolved_library
  resolved_library="$(LD_LIBRARY_PATH="$archive_root/RCMetaStudio/_internal:$archive_root/R/lib" ldd "$binary" | awk -v name="$soname" '$1 == name && $2 == "=>" { print $3; exit }')"
  case "$resolved_library" in
    "$archive_root/RCMetaStudio/_internal/"*) ;;
    *) die "Bundled runtime does not resolve $soname from the package (checking $binary): ${resolved_library:-missing}." ;;
  esac
}
for soname in libblas.so.3 liblapack.so.3 libgfortran.so.5 libgomp.so.1; do
  check_bundled_dependency "$matrix_library" "$soname"
done
check_bundled_dependency "$archive_root/R/library/tcltk/libs/tcltk.so" libtk8.6.so

cat > "$archive_root/LaunchRCMetaStudio.sh" <<'SH'
#!/bin/bash
set -euo pipefail
app_root="$(CDPATH= cd -- "${BASH_SOURCE[0]%/*}" && pwd -P)"
export R_HOME="$app_root/R"
export R_LIBS="$R_HOME/library"
export R_LIBS_USER="$R_LIBS"
export R_SHARE_DIR="$R_HOME/share"
export R_INCLUDE_DIR="$R_HOME/include"
export R_DOC_DIR="$R_HOME/doc"
export RPY2_CFFI_MODE=API
export LD_LIBRARY_PATH="$app_root/RCMetaStudio/_internal:$R_HOME/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PATH="$R_HOME/bin${PATH:+:$PATH}"
exec "$app_root/RCMetaStudio/RCMetaStudio" "$@"
SH
chmod +x "$archive_root/LaunchRCMetaStudio.sh"

step "Checking private R and Qt runtime before archiving"
env -u R_HOME -u R_LIBS -u R_LIBS_USER xvfb-run -a \
  env PATH="$r_home/bin" RCMS_REQUIRE_IN_PROCESS_RPY2=1 RPY2_CFFI_MODE=API \
  "$archive_root/LaunchRCMetaStudio.sh" \
    --automation-package-runtime-probe "$runtime_probe" \
    > "$runtime_probe_stdout" 2> "$runtime_probe_stderr"
[ -s "$runtime_probe" ] || die "Packaged runtime probe did not produce evidence."

step "Creating the portable tar.gz"
mkdir -p "$work_root/archive-staging"
mv "$archive_root" "$work_root/archive-staging/$artifact_name"
tar --sort=name --mtime='UTC 2020-01-01' --owner=0 --group=0 --numeric-owner \
  -czf "$artifact_path.tmp" -C "$work_root/archive-staging" "$artifact_name"
mv "$artifact_path.tmp" "$artifact_path"

step "Extracting the archive and running native package qualification"
extract_root="$qualification_root/extracted"
mkdir -p "$extract_root"
tar -xzf "$artifact_path" -C "$extract_root"
extracted_root="$extract_root/$artifact_name"
[ -x "$extracted_root/LaunchRCMetaStudio.sh" ] || die "Extracted Linux archive is missing its launcher."
mv "$r_home" "$work_root/r-home-hidden"
if ! env -u LD_LIBRARY_PATH xvfb-run -a env PATH="$extracted_root/R/bin" RCMS_REQUIRE_IN_PROCESS_RPY2=1 RPY2_CFFI_MODE=API \
  "$python_exe" "$repo_root/scripts/assemble_packaged_smoke_evidence.py" \
  --workflow-observation "$qualification_root/workflow-observation.json" \
  --surface-records "$qualification_root/surface-records.json" \
  --sample-observations "$qualification_root/sample-observations.json" \
  --sample BCG.rcms \
  --sample-root "$extracted_root/sample_projects" \
  --sample-path "$extracted_root/sample_projects/BCG.rcms" \
  --executable "$extracted_root/LaunchRCMetaStudio.sh" \
  --runtime-probe "$qualification_root/extracted-runtime-probe.json" \
  --surface-directory "$qualification_root/surfaces" \
  --log-path "$smoke_log" \
  --output "$smoke_evidence" \
  > "$qualification_root/packaged-smoke.stdout.log" \
  2> "$qualification_root/packaged-smoke.stderr.log"; then
  mv "$work_root/r-home-hidden" "$r_home"
  die "Extracted package smoke failed; see $qualification_root/packaged-smoke.stderr.log."
fi
if [ ! -s "$smoke_evidence" ]; then
  mv "$work_root/r-home-hidden" "$r_home"
  die "Extracted package smoke did not produce evidence."
fi
if ! env -u LD_LIBRARY_PATH -u RCMS_REQUIRE_IN_PROCESS_RPY2 xvfb-run -a \
  "$python_exe" "$repo_root/scripts/qualify_worker_journey.py" \
  --executable "$extracted_root/LaunchRCMetaStudio.sh" \
  --sample "$extracted_root/sample_projects/amino.rcms" \
  --destination "$qualification_root/worker-journey.rcms" \
  --output "$worker_evidence" \
  --artifact "$artifact_path" \
  > "$qualification_root/worker-journey.stdout.log" \
  2> "$qualification_root/worker-journey.stderr.log"; then
  mv "$work_root/r-home-hidden" "$r_home"
  die "Extracted package worker journey failed; see $qualification_root/worker-journey.stderr.log."
fi
mv "$work_root/r-home-hidden" "$r_home"
[ -s "$worker_evidence" ] || die "Extracted package worker journey did not produce evidence."

step "Recording artifact identity and runtime qualification"
"$python_exe" - "$artifact_path" "$evidence_path" "$qualification_root/extracted-runtime-probe.json" "$smoke_evidence" "$worker_evidence" "$r_deb_sha256" "$cursor_library_sha256" "$cursor_source" "$cursor_deb_sha256" "$linux_cran_repo" "${ID:-unknown}" "${VERSION_ID:-unknown}" "${PRETTY_NAME:-unknown}" "$host_glibc" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

artifact, evidence, probe, smoke, worker, r_sha, cursor_library_sha, cursor_source, cursor_deb_sha, repository, host_id, host_version, host_name, glibc = sys.argv[1:]
probe_data = json.loads(Path(probe).read_text(encoding="utf-8"))
smoke_data = json.loads(Path(smoke).read_text(encoding="utf-8"))
worker_data = json.loads(Path(worker).read_text(encoding="utf-8"))
if probe_data.get("schema_version") != 1:
    raise SystemExit("Packaged runtime probe has an unsupported record schema.")
if probe_data.get("project_schemas") != {
    "version": 2,
    "validated_members": ["manifest.json", "project.json", "state.json"],
}:
    raise SystemExit("Packaged runtime did not validate the current project schemas.")
digest = hashlib.sha256(Path(artifact).read_bytes()).hexdigest()
payload = {
    "schema_version": 1,
    "artifact": Path(artifact).name,
    "artifact_sha256": digest,
    "target": "ubuntu-24.04-x86_64",
    "build_host": {
        "id": host_id,
        "version": host_version,
        "pretty_name": host_name,
        "glibc": glibc,
    },
    "r_deb_sha256": r_sha,
    "xcb_cursor_library_sha256": cursor_library_sha,
    "xcb_cursor_source": cursor_source,
    "xcb_cursor_deb_sha256": cursor_deb_sha or None,
    "r_package_repository": repository,
    "runtime_probe": probe_data,
    "packaged_smoke": smoke_data,
    "worker_journey": worker_data,
    "qualification": "passed",
}
Path(evidence).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY

step "Linux package ready: $artifact_path"
