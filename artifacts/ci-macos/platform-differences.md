# Native setup differences

All supported targets use the 2026-11-13 Posit PPM snapshot and R 4.6.2. Live
repository indexes returned all 60 required CRAN roots on each target. Live
archive requests confirmed exact-version binaries for all 13 versioned CRAN
records. They returned tags 4.6-win, 4.6-macos-arm64 and 4.6-noble. The
manifest records SHA-256 pins for the seven authority archives per target.

| Branch | Reason |
| --- | --- |
| Common setup, hosted R | Source and Windows R-stack checks need a runner R installation. Packaging stages its own pinned runtime and CI-only Qt jobs use test backends. |
| Common setup, Windows rcc | The PyQt wheel ships Qt runtime libraries. Windows uses the official separately pinned Qt SDK rcc. |
| Common setup, macOS rcc | Apple silicon uses the official Qt Base SDK tool and verifies its native identity. |
| Common setup, Linux rcc | Linux obtains its prebuilt rcc from pinned PySide6 Essentials and runs native xcb checks. |
| Common setup, Linux package cache | Ubuntu Noble packaging is the Linux consumer of a private R closure. Linux source checks cover Qt and Python with R evidence skipped. |
| Windows artifact producer | Windows package and four R-stack matrix parts reuse one verified library and RCMetaR source build per workflow. R CMD check still tests the source archive. |
| PPM native Windows and macOS installation | R selects its native ZIP or TGZ repository transport and validates retained binary archive pins. |
| PPM Ubuntu Noble installation | The source-contrib URL transports prebuilt R binaries. The installer checks the binary response tag, installed versions and the retained authority archive digests. |
| Windows private R and package layout | The official signed Windows installer produces the private R tree, DLL layout and ZIP. |
| macOS private R and package layout | The authenticated CRAN R framework is staged as a relocatable arm64 framework in the app. |
| Linux private R and package layout | The pinned Posit DEB supplies relocatable R on the Ubuntu 24.04 glibc baseline. The portable archive bundles required ELF libraries. |
| macOS PR Qt wheel package | The distributed Qt 6.12 wheels require macOS 14.4. The release-grade Qt build targets macOS 14.0. |
| Native signing | macOS PR packaging verifies the ad-hoc app signature. Trusted release signs and notarizes the DMG. Windows and Linux retain their existing artifact and qualification contracts. |
| Staged R bridges | The worker migration handles removal of the embedded Python binding and the matching relocation steps. |
| Historical candidate revisions | Candidate builds for protected revisions predating the shared action still use the setup steps compatible with those sources. |

The setup action is shared by verification and current candidate builds.
Library caches identify the platform, R version, dependency policy and snapshot.
RCMetaR caches use a separate source key. Native package inspections retain the
same staging, runtime, extraction, test and provenance checks.
