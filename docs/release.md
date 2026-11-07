# Releasing RC MetaStudio

The release pipeline builds Windows x64, Apple silicon macOS, and Linux x86_64 artifacts once, qualifies those exact bytes, and promotes them without rebuilding. Linux packages target Ubuntu 24.04 x86_64 and contain the application, private R runtime, and launcher in a portable `.tar.gz`. Other Linux distributions are not release-qualified. Intel macOS is unsupported for future releases; historical assets remain unchanged.

## Prepare the source

1. Bump the version with `uv run python scripts/bump_version.py X.Y.Z`.
2. Complete the matching `CHANGELOG.md` section.
3. Run the fast, full R, Qt, and packaging checks affected by the release.
4. Merge the release commit to protected `master` and record its full commit SHA.
5. Confirm the `Qt6 Integration Verification` workflow succeeds for that SHA.

## Build a candidate

Run the `Build Immutable Candidate` workflow with:

- `version`: the full RC version, such as `0.4.0-rc.1`; its base must match the repository version
- `source_sha`: the full commit SHA on `master`
- `trust_profile`: `macos-trusted` for the normal signed macOS release path, or `unsigned-community` for an explicitly unsigned candidate

The workflow builds all three supported native targets and uploads a release-set manifest with the artifacts. Record the successful workflow run ID.

## Publish a release candidate

For the normal release path, run `Publish macOS-Trusted Release Candidate` with the candidate run ID, the same RC version, and the same source SHA. This workflow signs and notarizes the macOS application, creates its DMG, verifies the mounted application, checks Gatekeeper acceptance, qualifies the unchanged unsigned Windows and Linux artifacts, and publishes an immutable prerelease.

Use `Publish Unsigned Community Release Candidate` when all three artifacts are intentionally unsigned.

Dispatch publication from a branch or tag pointing to the exact selected source SHA. Publication rejects a different workflow-run SHA so GitHub provenance identifies the source actually qualified. Candidate builds may still select an older protected-master ancestor. Both consumers authenticate the candidate workflow's repository, event, path and protected-master revision before using its artifacts, and compare downloaded archives with their assembled records before extraction or signing.

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

Withdrawal requires a different, published stable replacement. It creates the tracking issue before editing the release. If issue creation fails, the release stays unchanged; if the release edit fails, the issue records the pending request. Rerun the same tag, replacement and reason to resume without duplicating the issue or notice. Requests for a tag are serialized; a conflicting retry fails for operator review.

Verification recomputes every stage link and validates nonempty output records. Promotion compares each downloaded archive and SBOM with its target's final attested outputs and requires provenance from the trusted publication workflow at the claimed source SHA. Promotion records the prior version so stable manifests retain the initial candidate identity; older stable manifests without that information may fail verification and are not rewritten.
