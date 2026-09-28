# Support Linux x86_64

## Status

Accepted. Supersedes the future release-target policy in [ADR-0012](0012-support-windows-and-apple-silicon-macos.md).

## Context

RC MetaStudio already builds release packages for Windows x64 and Apple silicon macOS. Linux users need an installable package with the same privately bundled R runtime and a native launcher. The project needs a bounded Linux baseline so the release can be built and tested on a stable, reproducible host.

## Decision

Future release sets require Windows x64, Apple silicon macOS, and Linux x86_64. The Linux package is a portable `RCMetaStudio-linux-x64.tar.gz`, built and qualified on Ubuntu 24.04 x86_64. It includes the application, private R runtime, and `LaunchRCMetaStudio.sh`.

The unsigned-community profile keeps all three platforms unsigned. The macos-trusted profile signs and notarizes the macOS application; Windows and Linux remain unsigned and are qualified, verified, and attested. Stable promotion requires that macos-trusted release set and carries the same three artifacts forward without rebuilding. Linux distributions other than Ubuntu 24.04 x86_64 are not release-qualified.

Intel macOS remains unsupported for future releases. Historical Intel macOS releases remain immutable and available, and source execution is not artificially blocked on Intel hardware.

## Consequences

- Every release-set manifest, candidate workflow, qualification path, SBOM, checksum list, attestation, and stable promotion includes Linux x86_64.
- Linux release assets use a portable tar archive and receive no platform signing or notarization.
- Ubuntu 24.04 x86_64 is the tested release baseline; broader distribution compatibility is not promised.
- Existing Windows and Apple silicon macOS artifact formats and trust stages remain in place.
