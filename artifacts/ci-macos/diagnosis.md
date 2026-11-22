# macOS packaging diagnosis

## Compilation and build inputs

The two full package jobs in the ten-run PR sample both missed the source-built
Qt SDK and PyQt wheel caches. A normal PR artifact now uses the exact PyQt6
6.12.0 and PyQt6-Qt6 6.12.0 wheels from uv.lock, with their published hashes.
Their native Qt deployment floor is macOS 14.4. The artifact name ends in
`-pr-wheels` and the bundle and Mach-O inspection enforce that floor. Nightly,
master, manual qualification and release candidates retain the source-built
Qt/PyQt profile and the 14.0 inspection floor.

| Build or install work | Baseline elapsed | PR change |
| --- | ---: | --- |
| qtbase, including qmake and rcc, first to last Ninja task | 11m 49s median, n=2 | Use the wheel runtime and prebuilt official rcc |
| qtsvg, first to last Ninja task | 22s median, n=2 | Use the wheel runtime |
| Qt source fetch, configure, compile and install, up to PyQt build | 13m 28s median, n=2 | No Qt SDK or tooling compilation |
| PyQt6 sdist to native wheel | 34m 37s median, n=2 | Use the locked PyQt6 wheel |
| RC MetaStudio editable Python wheel metadata | About 2s per package run | Retained, pure Python |
| CRAN dependency closure | 33s binary install median, n=2, zero source builds | Retain the dated Posit arm64 binary policy and archive hashes |
| RCMetaR source archive, R install and load verification | 16s median, n=2 | Cache the source archive and installed package by source, target and R policy |
| rpy2-rinterface native API build and install against staged R | 6s median, n=2 | Reuse the locked-source build from a package-specific uv cache |
| Qt forms and icon resource generation | About 4s in attached log | Retain generation with prebuilt tools |

The package logs reported 164 binary dependencies in the staged R closure and
no missing pinned binaries. RCMetaR declares no compiled code. R CMD INSTALL
byte-compiles its R code and builds its package databases. The published locked
rpy2-rinterface 3.6.7 universal2 wheel contains both ABI and API bindings and
its arm64 API binding links to the global R framework and BLAS. The package
requires one arm64 API bridge built against its private R framework. Retain
that build on a cache miss and keep its existing runtime, relocation and hash
checks. The source/platform job separately exercises an API build against its
runner-installed R. The API wheel build there took 9.5s median and editable
application wheel generation took 4.4s median, both across nine runs.
The focused contracts job showed no third-party compilation. All 79 locked
third-party packages selected for CPython 3.14 on macOS arm64 have compatible
wheel tags.

## Baseline

Ten consecutive PR workflow runs from `gh run list --workflow fast-verification.yml
--event pull_request --limit 10`. Per-run `gh run view RUN --log` supplies
sub-step timestamps and cache messages.
`gh api repos/AliSalman-et-al/rc-metastudio/actions/runs/RUN/jobs?per_page=100`
supplies job and step timestamps. The attached logs match run 45020115092.

| Run | Quick result from run creation | Workflow elapsed | Full macOS job |
| --- | ---: | ---: | ---: |
| 45020115092 | 4m 40s | 54m 52s | 50m 01s |
| 45016605972 | 3m 41s | 15m 18s | — |
| 45015177840 | 4m 23s | 15m 58s | — |
| 45014452775 | 4m 20s, failed | 4m 28s, failed | — |
| 45013207688 | 4m 15s | 70m 25s | 66m 01s |
| 45010348690 | — | 12m 24s | — |
| 45009729711 | 3m 05s | 16m 17s | — |
| 45008128112 | 4m 22s | 17m 46s | — |
| 45007556543 | — | 13m 13s | — |
| 44996938931 | — | 11m 21s, failed | — |

The quick signal is the Windows Quick Verification job completing. The workflow
elapsed is run creation to last update. Job elapsed is runner start to finish.
Compare end-to-end times against the two runs that selected the full macOS
package. Across those two, the quick signal median was 4m 28s and PR wall time
was 62m 39s. Both jobs queued for 3–4 seconds after the gate.

| Full macOS package step | Median baseline, n=2 |
| --- | ---: |
| Set up job | 2s |
| Checkout | 51s |
| uv and locked Python | 2s and 3s |
| Resolve package metadata and target | 1s each |
| Restore official Qt SDK and locate rcc | 4s and 1s |
| Fingerprint inputs and check both source caches | 4s, 1s and 1s |
| Build and run packaged workflow | 56m 32s |
| Prune wheel cache | 2s |
| Upload package and evidence | 6s and 4s |
| Post-step cleanup and cache saves | Under 10s |
| **Job** | **58m 01s** |

Inside the build, once Qt finished, R download/extraction and private runtime
setup took approximately 40 seconds. Staging adds about 30 seconds to the
binary dependency install and rpy2 build through closure pruning, relocation
and native proof. Form generation and PyInstaller took 33 seconds median.
Ad-hoc signature and verification took 11 seconds. Packaged Cocoa scale probes
took about 18 seconds, and the analysis and LaunchServices checks about
1m 50s. ZIP creation took 29 seconds and requalifying the exact extracted ZIP
took 2m 26s. These checks still run. Notarization and DMG creation belong to the
trusted release workflow.

| Other macOS jobs, median of 9 completed jobs | Source and platform | Focused packaging contracts |
| --- | ---: | ---: |
| Setup and checkout | 2s and 4s | 1s and 34s |
| uv and Python | 2s each | 2s each |
| Install pinned R | 60s | — |
| Default R library cache and native build prerequisites | 7s and 1s | — |
| rpy2 build, dependency sync and embedded R proof | 15s | — |
| Restore official Qt SDK and resolve rcc | 4s and <1s | — |
| Locked dependency sync | Included in bridge step | 5s |
| Native smoke / packaging contract tests | 40s | 7s |
| Cleanup | About 4s | About 2s |
| **Job** | **2m 36s** | **54s** |

The classifier already limited the full package to two of the ten PRs. Its
package-specific and shared CI/runtime rules stay in force. The focused job
tests native packaging contracts directly, while the source job checks Cocoa
and the system-R bridge, and the package job tests the frozen application.
