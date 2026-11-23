# Support qualified release platforms

## Status

Accepted. This consolidates the earlier Windows/Apple silicon policy and its Linux extension.

## Context

RC MetaStudio already builds release packages for Windows x64 and Apple silicon macOS. Linux users need an installable package with the same privately bundled R runtime and a native launcher. The project needs a bounded Linux baseline so the release can be built and tested on a stable, reproducible host.

## Decision

Release sets require Windows x64, Apple silicon macOS, and Linux x86_64. The Linux package is a portable `RCMetaStudio-linux-x64.tar.gz`, built and qualified on Ubuntu 24.04 x86_64. It includes the application, private R runtime, and `LaunchRCMetaStudio.sh`.

The unsigned-community profile keeps all three platforms unsigned. The macos-trusted profile signs and notarizes the macOS application; Windows and Linux remain unsigned and are qualified, verified, and attested. Stable promotion requires that macos-trusted release set and carries the same three artifacts forward without rebuilding. Linux distributions other than Ubuntu 24.04 x86_64 are not release-qualified.

Intel macOS remains unsupported for future releases. Historical Intel macOS releases remain immutable and available, and source execution is not artificially blocked on Intel hardware.

## Consequences

- Every release-set manifest, candidate workflow, qualification path, SBOM, checksum list, attestation, and stable promotion includes Linux x86_64.
- Linux release assets use a portable tar archive and receive no platform signing or notarization.
- Ubuntu 24.04 x86_64 is the tested release baseline; broader distribution compatibility is not promised.
- Existing Windows and Apple silicon macOS artifact formats and trust stages remain in place.

## Runtime collection and trust

- Ubuntu excludes the unused Qt TIFF plugin because it requests libtiff.so.5,
  which Noble lacks. Symbol stripping preserves the symbols required by
  dynamic lookup. Linux keeps upstream Rscript's option parser.
- Windows PyInstaller collection resolves API-set, UCRT and system ICU
  forwarders through the system so another toolchain on PATH cannot supply
  private copies. The Windows packaging wrapper supplies build
  roots to the authoritative PyInstaller spec.
- macOS sets the target deployment floor before native compilation. When
  the binary Qt wheel and SDK require a newer floor, build Qt at the app's
  floor and compile bindings against it with relocatable paths to one runtime.
  Serialize the C++ build to fit hosted-runner memory. Use a separate cache
  for the binding wheel so clearing an SDK staging tree cannot erase it.
- Assemble and qualify one private R framework before injecting it into the
  collected macOS app. A CRAN edge referring to /opt/R can resolve only
  to an identical authenticated framework member. Re-sign staged binaries
  ad hoc after architecture or install-name changes so they can run for proof
  before the final app signature.
- Developer ID members share a Team ID and use hardened runtime. Locally
  ad-hoc-signed members lack that shared identity, so hardened-runtime library
  validation on the local launcher would reject its bundled libpython.
  Sign nested members and bundles from the inside out. The outer signature
  owns the launcher's final context. Validate it there with strict deep
  verification, which also checks the nested members.
- Mach-O inspection preserves R's Java class resources. A Java class and a
  fat Mach-O can share the CAFEBABE header, so the magic bytes alone cannot
  identify the file as native code.

The candidate workflow may select an earlier protected-master revision.
Its target registry and fallbacks account for revisions before the macOS
resolver, independent SDK and binding caches, and verification recorder moved
or were introduced. The dispatch revision and selected build revision may
differ. Both must come from protected master. A withdrawal creates its audit
record before editing release state. A retry resumes from that pending record
if the edit failed.
