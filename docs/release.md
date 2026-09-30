# Releasing RC MetaStudio

The release pipeline builds Windows x64, Apple silicon macOS, and Linux x86_64 artifacts once. It qualifies those exact bytes and promotes them without rebuilding. Under [ADR0015](adr/0015-qualify-windows-macos-and-ubuntu.md), the 0.5.0 support policy targets Windows 10 version 1809 or later, macOS 14 or later on Apple silicon, and Ubuntu 24.04 and 26.04 LTS on x86_64. The Linux archive is built on Ubuntu 24.04 and contains the application, private R runtime, and launcher. Intel macOS and ARM Ubuntu remain outside the release scope.

## Prepare the source

1. Bump the version with `uv run python scripts/bump_version.py X.Y.Z`.
2. Complete the matching `CHANGELOG.md` section.
3. Run the fast, full R, Qt, and packaging checks affected by the release.
4. Merge the release commit to protected `master` and record its full commit SHA.
5. Confirm the `Qt6 Integration Verification` workflow succeeds for that SHA.

For the 0.5.0 workspace rewrite, complete the [native qualification matrix](qualification-evidence-2026-09-29.md) and [observed usability protocol](usability-qualification-protocol.md) before merging or publishing. A source process, a previous package revision, or a runner label does not qualify the final artifact. Record packaged journeys on Windows x64, Apple silicon macOS, Ubuntu 24.04 x64, and Ubuntu 26.04 x64. Check numerical results, saved-result portability, keyboard access, and platform assistive technology. Conduct the specified researcher usability sessions.

Intermediate package run `36714741801`, from source `a36c169`, passes all twenty registered journeys and 23 analysis runs on Windows build 26100, macOS 15.7.9 and 14.8.9 ARM64, and Ubuntu 24.04.5 and 26.04.1 x86_64. The exact archive hashes are recorded in the native qualification evidence. That revision still fails five Windows GUI sizing checks, and its macOS artifact is an unsigned ZIP. Windows 10 version 1809 has not been tested. No researcher or assistive-technology sessions have been observed. No final 0.5.0 candidate has passed the platform matrix. Keep each gap open until evidence for the final artifact closes it.

## Build a candidate

Run the `Build Immutable Candidate` workflow with:

- `version`: the full RC version, such as `0.4.0-rc.1`; its base must match the repository version
- `source_sha`: the full commit SHA on `master`
- `trust_profile`: `macos-trusted` for the normal signed macOS release path, or `unsigned-community` for an explicitly unsigned candidate

The workflow builds all three supported native targets and uploads a release-set manifest with the artifacts. Record the successful workflow run ID.

## Publish a release candidate

For the normal release path, run `Publish macOS-Trusted Release Candidate` with the candidate run ID, the same RC version, and the same source SHA. This workflow signs and notarizes the macOS application, creates its DMG, verifies the mounted application, checks Gatekeeper acceptance, and qualifies the unchanged unsigned Windows and Linux artifacts. It requires all twenty registered worker journeys from the finalized signed application on macOS 15 and from that exact DMG on macOS 14 before attestation and prerelease publication. These workflow requirements need passing run evidence; adding a job does not qualify an artifact.

Use `Publish Unsigned Community Release Candidate` when all three artifacts are intentionally unsigned.

Inspect the prerelease assets and checksums. Do not replace assets on an existing RC tag; build a new candidate and RC instead.

## Promote without rebuilding

Run `Promote Release Candidate` with the trusted RC tag and stable version. The workflow downloads the RC assets, verifies their digests, provenance, release-set state, and trust profile, then creates the stable release from the same bytes.

After promotion, confirm that the stable release contains:

- `RCMetaStudio-windows-x64.zip`
- `RCMetaStudio-macos-arm64.dmg`
- `RCMetaStudio-linux-x64.tar.gz`
- `SHA256SUMS`
- one SBOM for each platform
- `release-set-stable.json`

If a published release must be withdrawn, use the `Withdraw Release` workflow. It marks the release as a prerelease and records the superseding tag; it does not rewrite tags or delete historical artifacts.
