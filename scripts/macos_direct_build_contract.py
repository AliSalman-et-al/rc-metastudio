# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Source inputs and archive layout for direct macOS R provenance."""

import argparse
import shlex
from pathlib import Path

if __package__:
    from scripts import packaged_smoke_contract as smoke_contract, r_dependency_policy
    from scripts.resolve_macos_package_target import load_target
else:
    import packaged_smoke_contract as smoke_contract
    import r_dependency_policy
    from resolve_macos_package_target import load_target

ROOT = Path(__file__).resolve().parents[1]
_MACOS_ARM_TARGET = load_target("arm64")
DIRECT_R_OFFICIAL_INPUTS = {
    "macos-arm64": {
        "url": _MACOS_ARM_TARGET["r_url"],
        "sha256": _MACOS_ARM_TARGET["r_sha256"],
    },
}
R_BINARY_POLICY = r_dependency_policy.load_policy(ROOT / "config/r-dependencies.json")
DIRECT_R_PPM_SNAPSHOT: str = R_BINARY_POLICY["repository"]
RCMETAR_VERSION = next(
    line.removeprefix("Version:").strip()
    for line in (ROOT / "r/RCMetaR/DESCRIPTION").read_text(encoding="utf-8").splitlines()
    if line.startswith("Version:")
)
RCMETAR_ARCHIVE_NAME = f"RCMetaR-{RCMETAR_VERSION}-source.tar.gz"

DIRECT_BUILD_INPUT_MEMBERS = {
    "adapter_script": "qualification/embedded-r-adapter.py",
    "pre_normalization_audit": "qualification/direct-r-pre-normalization-audit.json",
    "normalized_adapter_map": "qualification/direct-r-adapter.json",
    "host_r_isolation_script": "qualification/macos-host-r-isolation.sh",
    "pyinstaller_toc_preflight": "qualification/verify-macos-r-pyinstaller-toc.py",
    "pyinstaller_toc_preflight_report": "qualification/macos-r-pyinstaller-toc-preflight.json",
    "explicit_r_toc": "qualification/direct-r-toc.json",
    "rpy2_api_build": "qualification/rpy2-api-build.json",
    "pre_sign_native_graph": "qualification/pre-sign-native-graph.json",
    "post_sign_native_inventory": "qualification/post-sign-native-inventory.json",
    "signing_inventory": "qualification/ad-hoc-signing-inventory.json",
    "ppm_archive_inventory": "qualification/ppm-archive-inventory.json",
    "rcmetar_source_archive": f"qualification/{RCMETAR_ARCHIVE_NAME}",
    "r_runtime_profile": "qualification/embedded-r-runtime-profile.json",
    "runtime_probe": "qualification/runtime-probe.json",
    "runtime_stdout": "qualification/runtime-probe.stdout.log",
    "runtime_stderr": "qualification/runtime-probe.stderr.log",
    "deployment_manifest": "qualification/deployment-manifest.json",
    "smoke_evidence": "qualification/packaged-smoke.json",
    "smoke_log": "qualification/packaged-smoke.log",
    "smoke_stdout": "qualification/packaged-smoke.stdout.log",
    "smoke_stderr": "qualification/packaged-smoke.stderr.log",
    "hang_trace": "qualification/packaged-smoke.hang-trace.log",
    "launchservices_marker": "qualification/launchservices-completion.json",
    "launchservices_stdout": "qualification/launchservices.stdout.log",
    "launchservices_stderr": "qualification/launchservices.stderr.log",
    "runner_environment": "qualification/runner-environment.json",
    "official_r_signature": "qualification/official-r-signature.json",
    **{
        f"surface_{scale_key}_{stream}": f"qualification/packaged-surface-{scale_key}.{stream}.log"
        for scale_key in (scale.replace(".", "") for scale in smoke_contract.SURFACE_SCALES)
        for stream in ("stdout", "stderr")
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=("macos-arm64",))
    args = parser.parse_args()
    values = {
        "pinned_cran_repo": DIRECT_R_PPM_SNAPSHOT,
        "ppm_contrib_path": R_BINARY_POLICY["platforms"][args.target]["contrib_path"],
        "rcmetar_archive_name": RCMETAR_ARCHIVE_NAME,
    }
    for name, value in values.items():
        print(f"{name}={shlex.quote(value)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
