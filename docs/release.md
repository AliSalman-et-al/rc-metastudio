# Releasing RC MetaStudio

The release pipeline builds Windows x64, Apple silicon macOS, and Linux x86_64 artifacts once, qualifies those exact bytes, and promotes them without rebuilding. Linux packages target Ubuntu 24.04 x86_64 and contain the application, private R runtime, and launcher in a portable `.tar.gz`. Other Linux distributions are not release-qualified. Intel macOS is unsupported for future releases; historical assets remain unchanged.

## Prepare the source

1. Bump the version with `uv run python scripts/bump_version.py X.Y.Z`.
2. Complete the matching `CHANGELOG.md` section.
3. Run the fast, full R, Qt, and packaging checks affected by the release.
4. Merge the release commit to protected `master` and record its full commit SHA.
5. Confirm the `Qt6 Integration Verification` workflow succeeds for that SHA.

For the 0.5.0 workspace rewrite, also complete the [native qualification matrix](qualification-evidence-2026-09-29.md) and [observed usability protocol](usability-qualification-protocol.md) before merging or publishing. A source process, a previous package revision, or a runner label does not qualify the final artifact. Record Windows x64, Apple silicon macOS, Ubuntu 24.04 x64, and Ubuntu 26.04 x64 packaged journeys; numerical and portable-result checks; keyboard and platform assistive-technology observations; and the specified researcher usability sessions. List unavailable evidence as outstanding rather than treating an automated proxy as a participant session.

## Build a candidate

Run the `Build Immutable Candidate` workflow with:

- `version`: the full RC version, such as `0.4.0-rc.1`; its base must match the repository version
- `source_sha`: the full commit SHA on `master`
- `trust_profile`: `macos-trusted` for the normal signed macOS release path, or `unsigned-community` for an explicitly unsigned candidate

The workflow builds all three supported native targets and uploads a release-set manifest with the artifacts. Record the successful workflow run ID.

## Publish a release candidate

For the normal release path, run `Publish macOS-Trusted Release Candidate` with the candidate run ID, the same RC version, and the same source SHA. This workflow signs and notarizes the macOS application, creates its DMG, verifies the mounted application, checks Gatekeeper acceptance, qualifies the unchanged unsigned Windows and Linux artifacts, and publishes an immutable prerelease.

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
