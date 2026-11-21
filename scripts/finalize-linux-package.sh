# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

step "Creating the portable tar.gz"
candidate_dir="$(mktemp -d "$artifact_dir/.linux-candidate.XXXXXX")"
candidate_archive="$candidate_dir/$artifact_name.tar.gz"
candidate_evidence="$candidate_dir/qualification.json"
retain_failed_candidate() {
  status=$?
  if [ "$status" -ne 0 ]; then
    cp -R "$qualification_root" "$candidate_dir/qualification" || true
  fi
  exit "$status"
}
trap retain_failed_candidate EXIT
mkdir -p "$work_root/archive-staging"
mv "$archive_root" "$work_root/archive-staging/$artifact_name"
tar --sort=name --mtime='UTC 2020-01-01' --owner=0 --group=0 --numeric-owner \
  -I 'gzip -9' -cf "$candidate_archive" -C "$work_root/archive-staging" "$artifact_name"


step "Extracting the archive and running native package qualification"
extract_root="$qualification_root/extracted"
mkdir -p "$extract_root"
tar -xzf "$candidate_archive" -C "$extract_root"
extracted_root="$extract_root/$artifact_name"
[ -x "$extracted_root/LaunchRCMetaStudio.sh" ] || die "Extracted Linux archive is missing its launcher."
mv "$r_home" "$work_root/r-home-hidden"
if ! env -u LD_LIBRARY_PATH xvfb-run -a env PATH="$extracted_root/R/bin" RCMS_REQUIRE_IN_PROCESS_RPY2=1 RPY2_CFFI_MODE=API \
  "$python_exe" "$repo_root/scripts/assemble_packaged_smoke_evidence.py" \
  --workflow-observation "$qualification_root/workflow-observation.json" \
  --surface-records "$qualification_root/surface-records.json" \
  --sample-observations "$qualification_root/sample-observations.json" \
  --sample "Binary - BCG vaccine and tuberculosis.rcms" \
  --sample-root "$extracted_root/sample_projects" \
  --sample-path "$extracted_root/sample_projects/Binary - BCG vaccine and tuberculosis.rcms" \
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
mv "$work_root/r-home-hidden" "$r_home"
[ -s "$smoke_evidence" ] || die "Extracted package smoke did not produce evidence."

step "Recording artifact identity and runtime qualification"
"$python_exe" - "$candidate_archive" "$candidate_evidence" "$qualification_root/extracted-runtime-probe.json" "$smoke_evidence" "$r_deb_sha256" "$cursor_library_sha256" "$cursor_source" "$cursor_deb_sha256" "$linux_cran_repo" "${ID:-unknown}" "${VERSION_ID:-unknown}" "${PRETTY_NAME:-unknown}" "$host_glibc" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

artifact, evidence, probe, smoke, r_sha, cursor_library_sha, cursor_source, cursor_deb_sha, repository, host_id, host_version, host_name, glibc = sys.argv[1:]
probe_data = json.loads(Path(probe).read_text(encoding="utf-8"))
smoke_data = json.loads(Path(smoke).read_text(encoding="utf-8"))
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
    "qualification": "passed",
}
Path(evidence).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY

mv "$candidate_archive" "$artifact_path"
mv "$candidate_evidence" "$evidence_path"

step "Linux package ready: $artifact_path"
