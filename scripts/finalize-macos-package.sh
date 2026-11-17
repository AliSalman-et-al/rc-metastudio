# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

candidate_dir="$(mktemp -d "$artifact_dir/.macos-candidate.XXXXXX")"
tmp_zip_path="$candidate_dir/$artifact_name.zip"
final_archive_inspection_path="$archive_inspection_path"
final_qualification_evidence_path="$qualification_evidence_path"
archive_inspection_path="$candidate_dir/$artifact_name-archive-inspection.json"
qualification_evidence_path="$candidate_dir/$artifact_name-evidence.json"
retain_failed_candidate() {
  status=$?
  if [ "$status" -ne 0 ]; then
    cp -R "$qualification_root" "$candidate_dir/qualification" || true
  fi
  exit "$status"
}
trap retain_failed_candidate EXIT
(
  step "Creating macOS artifact ZIP"
  rm -rf "$archive_staging_root"
  copy_tree "$app_bundle" "$archive_root_dir/RCMetaStudio.app"
  copy_tree "$qualification_root" "$archive_root_dir/qualification"
  ditto -c -k --norsrc --keepParent "$archive_root_dir" "$tmp_zip_path"
)

python3 - "$tmp_zip_path" "$archive_root_name" "$skip_smoke" "$r_framework_version" <<'PY'
import stat
import sys
import zipfile

zip_path = sys.argv[1]
archive_root_name = sys.argv[2].rstrip("/")
skip_smoke = sys.argv[3] == "1"
framework_version = sys.argv[4]
framework = f"{archive_root_name}/RCMetaStudio.app/Contents/Frameworks/R.framework"
version_root = f"{framework}/Versions/{framework_version}"
resources = f"{version_root}/Resources"
required = [
    f"{archive_root_name}/RCMetaStudio.app/Contents/MacOS/RCMetaStudio",
    f"{archive_root_name}/RCMetaStudio.app/Contents/Resources/sample_projects/BCG.rcms",
    f"{archive_root_name}/RCMetaStudio.app/Contents/Resources/sample_projects/amino.rcms",
    f"{resources}/bin/Rscript",
    f"{resources}/library/RCMetaR/DESCRIPTION",
    f"{resources}/Info.plist",
    f"{version_root}/R",
    f"{archive_root_name}/qualification/ad-hoc-signing-inventory.json",
    f"{archive_root_name}/RCMetaStudio.app/Contents/Resources/LaunchRCMetaStudio.command",
    f"{archive_root_name}/qualification/deployment-manifest.json",
    f"{archive_root_name}/qualification/runtime-probe.json",
    f"{archive_root_name}/qualification/embedded-r-runtime-profile.json",
    f"{archive_root_name}/qualification/direct-r-build-manifest.json",
]
expected_links = {
    f"{framework}/Versions/Current": framework_version,
    f"{framework}/Resources": "Versions/Current/Resources",
    f"{resources}/lib/libR.dylib": "../../R",
    f"{framework}/R": "Versions/Current/R",
}
required.extend(expected_links)
if not skip_smoke:
    required.extend([
        f"{archive_root_name}/qualification/packaged-smoke.json",
        f"{archive_root_name}/qualification/packaged-smoke.log",
        f"{archive_root_name}/qualification/launchservices-completion.json",
        f"{archive_root_name}/qualification/packaged-smoke.stdout.log",
        f"{archive_root_name}/qualification/packaged-smoke.stderr.log",
        f"{archive_root_name}/qualification/packaged-smoke.hang-trace.log",
    ])
with zipfile.ZipFile(zip_path) as archive:
    names = set(archive.namelist())
    info_by_name = {info.filename: info for info in archive.infolist()}
    for path, target in expected_links.items():
        if path not in info_by_name:
            continue
        info = info_by_name[path]
        mode = info.external_attr >> 16
        if (
            not stat.S_ISLNK(mode)
            or archive.read(path).decode("utf-8") != target
        ):
            raise SystemExit(f"Created ZIP has a noncanonical R framework alias: {path}")
outside_root = [
    name for name in names if name and not name.startswith(f"{archive_root_name}/")
]
if outside_root:
    raise SystemExit(
        "Created ZIP has entries outside "
        f"{archive_root_name}: " + ", ".join(sorted(outside_root)[:10])
    )
missing = [path for path in required if path not in names]
if missing:
    raise SystemExit("Created ZIP is missing: " + ", ".join(missing))
PY

if [ "$skip_smoke" -eq 0 ]; then
  "$python_exe" "$repo_root/scripts/inspect_macos_deployment.py" archive \
    --target "macos-$architecture" \
    --archive "$tmp_zip_path" --archive-root-name "$archive_root_name" \
    --deployment-manifest "$deployment_manifest_path" \
    --signing-inventory "$signing_inventory_path" \
    --runtime-probe "$runtime_probe_path" \
    --runtime-stdout "$runtime_stdout_path" --runtime-stderr "$runtime_stderr_path" \
    --r-runtime-profile "$r_runtime_profile_path" \
    --direct-build-manifest "$r_direct_build_manifest_path" \
    --smoke-evidence "$smoke_evidence_path" --smoke-log "$smoke_log_path" \
    --smoke-stdout "$smoke_stdout_path" --smoke-stderr "$smoke_stderr_path" \
    --hang-trace "$hang_trace_path" \
    --launchservices-marker "$launchservices_marker_path" \
    --output "$archive_inspection_path"
fi

if [ "$skip_smoke" -eq 0 ]; then
  step "Extracting the exact ZIP and requalifying its normal app entry"
  extracted_root="$work_root/extracted-qualification"
  rm -rf "$extracted_root"
  mkdir -p "$extracted_root"
  ditto -x -k "$tmp_zip_path" "$extracted_root"
  extracted_app="$extracted_root/$archive_root_name/RCMetaStudio.app"
  extracted_probe="$qualification_root/extracted-runtime-probe.json"
  extracted_manifest="$qualification_root/extracted-deployment-manifest.json"
  extracted_smoke="$qualification_root/extracted-packaged-smoke.json"
  extracted_workflow="$qualification_root/extracted-workflow-observation.json"
  extracted_surfaces="$qualification_root/extracted-surface-records"
  extracted_samples="$qualification_root/extracted-sample-observations.json"
  extracted_smoke_log="$qualification_root/extracted-packaged-smoke.log"
  extracted_stdout="$qualification_root/extracted-packaged-smoke.stdout.log"
  extracted_stderr="$qualification_root/extracted-packaged-smoke.stderr.log"
  extracted_hang_trace="$qualification_root/extracted-packaged-smoke.hang-trace.log"
  extracted_marker="$qualification_root/extracted-launchservices-completion.json"
  extracted_pid="$qualification_root/extracted-launchservices.pid"
  extracted_r_home="$extracted_app/Contents/Frameworks/R.framework/Resources"
  extracted_r_lib="$extracted_r_home/library"
  [ -x "$extracted_app/Contents/MacOS/RCMetaStudio" ] || { echo "Exact ZIP extraction lacks the app entry executable." >&2; exit 1; }
  [ -x "$extracted_r_home/bin/Rscript" ] || { echo "Exact ZIP extraction lacks private R." >&2; exit 1; }
  run_extracted() {
    env -u QT_QPA_PLATFORM RCMS_REQUIRE_IN_PROCESS_RPY2=1 RPY2_CFFI_MODE=API \
      RCMS_R_HOME="$extracted_r_home" RCMS_R_LIBS="$extracted_r_lib" \
      "$python_exe" "$repo_root/scripts/run_bounded_process.py" --timeout-seconds 900 \
      --stdout "$extracted_stdout" --stderr "$extracted_stderr" -- "$@"
  }
  : > "$extracted_hang_trace"
  run_extracted "$extracted_app/Contents/MacOS/RCMetaStudio" --automation-package-runtime-probe "$extracted_probe"
  surface_scales="$("$python_exe" "$repo_root/scripts/packaged_smoke_contract.py")"
  while IFS= read -r scale; do
    QT_SCALE_FACTOR="$scale" RCMS_PACKAGE_BASELINE_DPR="$("$python_exe" -c 'import json,sys; print(json.load(open(sys.argv[1]))["qt"]["baseline_device_pixel_ratio"])' "$extracted_probe")" \
      RCMS_AUTOMATION_SMOKE_LOG="$extracted_smoke_log" RCMS_PACKAGED_PROCESS_TIMEOUT_SECONDS=60 \
      run_extracted "$extracted_app/Contents/MacOS/RCMetaStudio" --automation-package-surface-smoke "$extracted_surfaces/surface-$scale.json" "$scale"
  done <<< "$surface_scales"
  mkdir -p "$extracted_surfaces"
  env -u QT_QPA_PLATFORM \
    RCMS_REQUIRE_IN_PROCESS_RPY2=1 \
    RPY2_CFFI_MODE=API \
    RCMS_R_HOME="$extracted_r_home" \
    RCMS_R_LIBS="$extracted_r_lib" \
    "$python_exe" "$repo_root/scripts/assemble_packaged_smoke_evidence.py" \
    --workflow-observation "$extracted_workflow" \
    --surface-records "$extracted_surfaces" \
    --sample-observations "$extracted_samples" \
    --sample BCG.rcms --sample-root "$extracted_app/Contents/Resources/sample_projects" \
    --sample-path "$extracted_app/Contents/Resources/sample_projects/BCG.rcms" \
    --executable "$extracted_app/Contents/MacOS/RCMetaStudio" \
    --runtime-probe "$extracted_probe" --surface-directory "$extracted_surfaces" \
    --log-path "$extracted_smoke_log" \
    --output "$extracted_smoke"
  rm -f "$extracted_marker" "$extracted_pid"
  env -u QT_QPA_PLATFORM RCMS_REQUIRE_IN_PROCESS_RPY2=1 RPY2_CFFI_MODE=API \
    RCMS_R_HOME="$extracted_r_home" RCMS_R_LIBS="$extracted_r_lib" RCMS_STARTUP_PROJECT_SMOKE=1 \
    RCMS_AUTOMATION_SMOKE_LOG="$extracted_smoke_log" RCMS_STARTUP_COMPLETION_MARKER="$extracted_marker" \
    RCMS_AUTOMATION_PID_FILE="$extracted_pid" "$python_exe" "$repo_root/scripts/run_bounded_process.py" \
      --timeout-seconds 900 --stdout "$extracted_stdout" --stderr "$extracted_stderr" --owned-pid-file "$extracted_pid" -- \
      open -W -n "$extracted_app" --args --automation-startup-project-smoke \
        --automation-startup-completion-marker "$extracted_marker" --automation-pid-file "$extracted_pid" \
        --automation-smoke-log "$extracted_smoke_log" "$extracted_app/Contents/Resources/sample_projects/BCG.rcms"
  "$python_exe" "$repo_root/scripts/inspect_macos_deployment.py" finalize-smoke \
    --smoke-evidence "$extracted_smoke" --smoke-log "$extracted_smoke_log" --launchservices-marker "$extracted_marker" \
    --require-atomic-completion
  rm -f "$extracted_pid"
  "$python_exe" "$repo_root/scripts/inspect_macos_deployment.py" inspect \
    --target "macos-$architecture" --app-root "$extracted_app" \
    --output "$extracted_manifest" --source-commit "$source_commit" \
    --runtime-probe "$extracted_probe" --signing-inventory "$signing_inventory_path" \
    --locked-qt-root "$locked_qt_root" --python-version "$python_version" \
    --pyqt6-version "$pyqt6_version" --qt-version "$qt_version" \
    --sip-version "$sip_version" --sip-runtime-version "$sip_runtime_version" \
    --r-version "$r_version" --rpy2-version "$rpy2_version" --pyinstaller-version 6.22.3
  "$python_exe" "$repo_root/scripts/inspect_macos_deployment.py" evidence \
    --target "macos-$architecture" --archive "$tmp_zip_path" \
    --deployment-manifest "$deployment_manifest_path" --signing-inventory "$signing_inventory_path" \
    --runtime-probe "$runtime_probe_path" --r-runtime-profile "$r_runtime_profile_path" \
    --direct-build-manifest "$r_direct_build_manifest_path" \
    --smoke-evidence "$smoke_evidence_path" --smoke-log "$smoke_log_path" \
    --smoke-stdout "$smoke_stdout_path" --smoke-stderr "$smoke_stderr_path" \
    --hang-trace "$hang_trace_path" --launchservices-marker "$launchservices_marker_path" \
    --extracted-runtime-probe "$extracted_probe" --extracted-deployment-manifest "$extracted_manifest" \
    --extracted-smoke-evidence "$extracted_smoke" --extracted-smoke-log "$extracted_smoke_log" \
    --extracted-smoke-stdout "$extracted_stdout" --extracted-smoke-stderr "$extracted_stderr" \
    --extracted-hang-trace "$extracted_hang_trace" --extracted-launchservices-marker "$extracted_marker" \
    --archive-inspection "$archive_inspection_path" --output "$qualification_evidence_path"
fi

mv "$tmp_zip_path" "$zip_path"
if [ "$skip_smoke" -eq 0 ]; then
  mv "$archive_inspection_path" "$final_archive_inspection_path"
  mv "$qualification_evidence_path" "$final_qualification_evidence_path"
fi
echo "Created $zip_path"
