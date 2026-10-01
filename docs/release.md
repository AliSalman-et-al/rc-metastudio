# Releasing RC MetaStudio

The release pipeline builds Windows x64, Apple silicon macOS, and Linux x86_64 artifacts once. It qualifies those exact bytes and promotes them without rebuilding. Under [ADR0015](adr/0015-qualify-windows-macos-and-ubuntu.md), the 0.5.0 support policy targets Windows 10 version 1809 or later, macOS 14 or later on Apple silicon, and Ubuntu 24.04 and 26.04 LTS on x86_64. The Linux archive is built on Ubuntu 24.04 and contains the application, private R runtime, and launcher. Intel macOS and ARM Ubuntu remain outside the release scope.

## Prepare the source

1. Bump the version with `uv run python scripts/bump_version.py X.Y.Z`.
2. Complete the matching `CHANGELOG.md` section.
3. Run the fast, full R, Qt, and packaging checks affected by the release.
4. Merge the release commit to protected `master` and record its full commit SHA.
5. Confirm the `Qt6 Integration Verification` workflow succeeds for that SHA.

For future releases, complete the [native qualification matrix](qualification-evidence-2026-09-29.md) and [observed usability protocol](usability-qualification-protocol.md) before merging or publishing. A source process, a previous package revision, or a runner label does not qualify the final artifact. Record packaged journeys on Windows x64, Apple silicon macOS, Ubuntu 24.04 x64, and Ubuntu 26.04 x64. Check numerical results, saved-result portability, keyboard access, and platform assistive technology. Conduct the specified researcher usability sessions. Version 0.5.0 was published with Windows 10 version 1809, platform assistive technology, and researcher usability still unobserved; its publication does not qualify those observations.

### Stable 0.5.0 publication

Stable [0.5.0](https://github.com/AliSalman-et-al/rc-metastudio/releases/tag/v0.5.0)
was published on 2026-10-01 from source
[`86ea34b64eedfbd920d498c054651e050a1e2d78`](https://github.com/AliSalman-et-al/rc-metastudio/commit/86ea34b64eedfbd920d498c054651e050a1e2d78).
Candidate run [36806312655](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36806312655)
built immutable candidate `v0.5.0-rc.1`; trusted publisher run
[36817462678](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36817462678)
and promotion run
[36825859230](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36825859230)
both succeeded on attempt 2. Stable promotion reused the trusted RC artifacts
without rebuilding. The exact final macOS DMG passed 48 registered journeys
and 58 analysis runs on macOS 15 and 14; the retained results also pass five
matched saved-project cases. Windows x64 and Ubuntu 24.04/26.04 package
qualification passed. See the [qualification record](qualification-evidence-2026-09-29.md)
for per-platform run evidence and digests. Windows 10 version 1809, platform
assistive technology, and researcher usability sessions remain unobserved.
Issue [#498](https://github.com/AliSalman-et-al/rc-metastudio/issues/498)
remains open.

## Build a candidate

Run the `Build Immutable Candidate` workflow with:

- `version`: the full RC version, such as `0.4.0-rc.1`; its base must match the repository version
- `source_sha`: the full commit SHA on `master`
- `trust_profile`: `macos-trusted` for the normal signed macOS release path, or `unsigned-community` for an explicitly unsigned candidate

The workflow builds all three supported native targets and uploads a release-set manifest with the artifacts. Record the successful workflow run ID.

## Publish a release candidate

For the normal release path, run `Publish macOS-Trusted Release Candidate` with the candidate run ID, the same RC version, and the same source SHA. This workflow signs and notarizes the macOS application, creates its DMG, verifies the mounted application, checks Gatekeeper acceptance, and qualifies the unchanged unsigned Windows and Linux artifacts. It requires all registered worker journeys (currently 48, covering the 44 desktop method/workflow cells and special journeys) from the finalized signed application on macOS 15 and from that exact DMG on macOS 14 before attestation and prerelease publication. These workflow requirements need passing run evidence; adding a job does not qualify an artifact.

Use `Publish Unsigned Community Release Candidate` when all three artifacts are intentionally unsigned.

Inspect the prerelease assets and checksums. Do not replace assets on an existing RC tag; build a new candidate and RC instead.

When publishing a source commit that changed workflows, GitHub can deny release
creation for a new tag despite `contents: write`. See GitHub's
[workflow permission requirement](https://github.blog/changelog/2023-11-02-github-actions-enforcing-workflow-scope-when-creating-a-release/).
An authorized maintainer can create the intended RC or stable tag at the exact
source commit in the verified release manifest, then rerun the failed publication
job. The workflow verifies the existing tag's commit before publishing. Both
0.5.0 publication jobs recovered this way, using their existing artifacts.

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
