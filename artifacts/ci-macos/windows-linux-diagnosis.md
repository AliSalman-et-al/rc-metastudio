# Windows and Linux CI baseline

The same ten consecutive PR runs listed in [diagnosis.md](diagnosis.md) supply Actions timestamps and step logs. Medians below use successful jobs and successful executed steps only. Cache counts include observed restore and miss messages. The Actions API omits skipped steps from the elapsed sample.

## Qt6 Verification Change Classifier

| Step | Median (s) | Samples |
| --- | ---: | ---: |
| **Job** | 8 | 9 |
| Runner queue | 3 | 9 |
| Set up job | 1 | 9 |
| Check out classifier policy | 3 | 7 |
| Classify changed paths | 0 | 9 |
| Plan R Stack checks and desktop shards | 0 | 7 |
| Post Check out classifier policy | 1 | 7 |
| Complete job | 0 | 9 |
| Check out classifier policy and comparison history | 19 | 2 |
| Post Check out classifier policy and comparison history | 0.5 | 2 |

## Native Qt6 Remaining Surfaces

| Step | Median (s) | Samples |
| --- | ---: | ---: |
| **Job** | 98.5 | 8 |
| Runner queue | 2 | 8 |
| Set up job | 1 | 8 |
| Check out repository | 7.5 | 8 |
| Install uv | 4 | 8 |
| Install Python | 3 | 8 |
| Cache official Qt rcc package | 1 | 8 |
| Run remaining-surface verification on a fresh runner | 73 | 8 |
| Upload native remaining-surface evidence | 1 | 8 |
| Prune uv cache | 1 | 8 |
| Post Cache official Qt rcc package | 0 | 8 |
| Post Install uv | 0 | 8 |
| Post Check out repository | 2 | 8 |
| Complete job | 0 | 8 |

| Cache step | Hits | Misses |
| --- | ---: | ---: |
| uv | 7 | 0 |
| Actions cache | 7 | 0 |
| Install uv | 1 | 0 |
| Cache official Qt rcc package | 1 | 0 |

## Required Windows Full R Stack Evidence (1)

| Step | Median (s) | Samples |
| --- | ---: | ---: |
| **Job** | 621 | 8 |
| Runner queue | 2.5 | 8 |
| Set up job | 2 | 8 |
| Check out repository | 7.5 | 8 |
| Install uv | 4.5 | 8 |
| Install Python | 3 | 8 |
| Install pinned R | 22 | 8 |
| Install PDF text verification tool | 17 | 8 |
| Cache official Qt rcc package | 11 | 8 |
| Run Full R Stack Evidence | 520 | 8 |
| Upload Full R Stack evidence | 20 | 8 |
| Prune uv cache | 1 | 8 |
| Post Cache official Qt rcc package | 0 | 8 |
| Post Install uv | 0 | 8 |
| Post Check out repository | 2 | 8 |
| Complete job | 0 | 8 |

| Cache step | Hits | Misses |
| --- | ---: | ---: |
| uv | 7 | 0 |
| Actions cache | 7 | 0 |
| Install uv | 1 | 0 |
| Cache official Qt rcc package | 1 | 0 |

## Native Qt6 Vertical Slice

| Step | Median (s) | Samples |
| --- | ---: | ---: |
| **Job** | 180 | 8 |
| Runner queue | 2 | 8 |
| Set up job | 1.5 | 8 |
| Check out repository | 7.5 | 8 |
| Install uv | 4.5 | 8 |
| Install Python | 3.5 | 8 |
| Cache official Qt rcc package | 1 | 8 |
| Run Native Qt6 Vertical Slice | 153.5 | 8 |
| Upload native calculator evidence | 1 | 8 |
| Prune uv cache | 1 | 8 |
| Post Cache official Qt rcc package | 0 | 8 |
| Post Install uv | 0 | 8 |
| Post Check out repository | 2.5 | 8 |
| Complete job | 0 | 8 |

| Cache step | Hits | Misses |
| --- | ---: | ---: |
| uv | 7 | 0 |
| Actions cache | 7 | 0 |
| Install uv | 1 | 0 |
| Cache official Qt rcc package | 1 | 0 |

## Required Windows Full R Stack Evidence (2)

| Step | Median (s) | Samples |
| --- | ---: | ---: |
| **Job** | 575.5 | 8 |
| Runner queue | 2 | 8 |
| Set up job | 2 | 8 |
| Check out repository | 7 | 8 |
| Install uv | 4 | 8 |
| Install Python | 4 | 8 |
| Install pinned R | 22 | 8 |
| Install PDF text verification tool | 16 | 8 |
| Cache official Qt rcc package | 11 | 8 |
| Run Full R Stack Evidence | 483 | 8 |
| Upload Full R Stack evidence | 18 | 8 |
| Prune uv cache | 1 | 8 |
| Post Cache official Qt rcc package | 0 | 8 |
| Post Install uv | 0 | 8 |
| Post Check out repository | 2 | 8 |
| Complete job | 0 | 8 |

| Cache step | Hits | Misses |
| --- | ---: | ---: |
| uv | 7 | 0 |
| Actions cache | 7 | 0 |
| Install uv | 1 | 0 |
| Cache official Qt rcc package | 1 | 0 |

## Source and Platform Verification (linux-x64)

| Step | Median (s) | Samples |
| --- | ---: | ---: |
| **Job** | 48 | 8 |
| Runner queue | 2 | 8 |
| Set up job | 2 | 8 |
| Check out repository | 4 | 8 |
| Install uv | 1 | 8 |
| Install locked Python | 1 | 8 |
| Run Linux Qt xcb and Python verification | 35 | 8 |
| Prune uv cache | 0 | 8 |
| Post Install uv | 0 | 8 |
| Post Check out repository | 0.5 | 8 |
| Complete job | 0 | 8 |

| Cache step | Hits | Misses |
| --- | ---: | ---: |
| uv | 6 | 1 |
| Install uv | 1 | 0 |

## Required Windows Full R Stack Evidence (checks)

| Step | Median (s) | Samples |
| --- | ---: | ---: |
| **Job** | 423.5 | 8 |
| Runner queue | 2.5 | 8 |
| Set up job | 2 | 8 |
| Check out repository | 7 | 8 |
| Install uv | 5 | 8 |
| Install Python | 3.5 | 8 |
| Install pinned R | 23.5 | 8 |
| Cache official Qt rcc package | 10.5 | 8 |
| Run Full R Stack Evidence | 359.5 | 8 |
| Upload Full R Stack evidence | 1 | 8 |
| Upload strict golden capture | 2.5 | 8 |
| Prune uv cache | 1 | 8 |
| Post Cache official Qt rcc package | 0 | 8 |
| Post Install uv | 0 | 8 |
| Post Check out repository | 2 | 8 |
| Complete job | 0 | 8 |

| Cache step | Hits | Misses |
| --- | ---: | ---: |
| uv | 7 | 0 |
| Actions cache | 7 | 0 |
| Install uv | 1 | 0 |
| Cache official Qt rcc package | 1 | 0 |

## Required Windows Full R Stack Evidence (3)

| Step | Median (s) | Samples |
| --- | ---: | ---: |
| **Job** | 636.5 | 8 |
| Runner queue | 2 | 8 |
| Set up job | 2 | 8 |
| Check out repository | 8 | 8 |
| Install uv | 4 | 8 |
| Install Python | 4 | 8 |
| Install pinned R | 24 | 8 |
| Install PDF text verification tool | 16 | 8 |
| Cache official Qt rcc package | 11 | 8 |
| Run Full R Stack Evidence | 544.5 | 8 |
| Upload Full R Stack evidence | 18.5 | 8 |
| Prune uv cache | 1 | 8 |
| Post Cache official Qt rcc package | 0 | 8 |
| Post Install uv | 0 | 8 |
| Post Check out repository | 2.5 | 8 |
| Complete job | 0 | 8 |

| Cache step | Hits | Misses |
| --- | ---: | ---: |
| uv | 7 | 0 |
| Actions cache | 7 | 0 |
| Install uv | 1 | 0 |
| Cache official Qt rcc package | 1 | 0 |

## Source and Platform Verification (windows-x64)

| Step | Median (s) | Samples |
| --- | ---: | ---: |
| **Job** | 195.5 | 8 |
| Runner queue | 2.5 | 8 |
| Set up job | 2 | 8 |
| Check out repository | 22 | 8 |
| Install uv | 4.5 | 8 |
| Install locked Python | 1.5 | 8 |
| Install pinned R | 22 | 8 |
| Cache Default R Evidence library | 1 | 8 |
| Cache official Qt rcc package on Windows | 10 | 8 |
| Run Platform-Neutral Python Verification | 125 | 8 |
| Prune uv cache | 1 | 8 |
| Post Cache official Qt rcc package on Windows | 0 | 8 |
| Post Cache Default R Evidence library | 0 | 8 |
| Post Install uv | 0 | 8 |
| Post Check out repository | 2 | 8 |
| Complete job | 0 | 8 |

| Cache step | Hits | Misses |
| --- | ---: | ---: |
| uv | 7 | 0 |
| Actions cache | 7 | 7 |
| Install uv | 1 | 0 |
| Cache Default R Evidence library | 0 | 1 |
| Cache official Qt rcc package on Windows | 1 | 0 |

## Required Windows x64 Package Qualification / RCMetaStudio Windows x64

| Step | Median (s) | Samples |
| --- | ---: | ---: |
| **Job** | 699 | 8 |
| Runner queue | 2 | 8 |
| Set up job | 1 | 8 |
| Run actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 | 23 | 8 |
| Run astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b | 5 | 8 |
| Run uv python install | 1 | 8 |
| Resolve authoritative package version | 3 | 8 |
| Cache immutable official R download | 2 | 8 |
| Build and qualify the public Windows package command | 652 | 8 |
| Upload package and qualification evidence | 3 | 8 |
| Post Cache immutable official R download | 0 | 8 |
| Post Run astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b | 0 | 8 |
| Post Run actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 | 2 | 8 |
| Complete job | 0 | 8 |

| Cache step | Hits | Misses |
| --- | ---: | ---: |
| uv | 8 | 0 |
| Actions cache | 8 | 0 |

## Qt6 Integration Verification Gate

| Step | Median (s) | Samples |
| --- | ---: | ---: |
| **Job** | 4 | 8 |
| Runner queue | 2.5 | 8 |
| Set up job | 0 | 8 |
| Check required lane results | 0 | 8 |
| Complete job | 0 | 8 |

## Quick Verification

| Step | Median (s) | Samples |
| --- | ---: | ---: |
| **Job** | 255.5 | 6 |
| Runner queue | 2 | 6 |
| Set up job | 1.5 | 6 |
| Check out repository | 21 | 6 |
| Install uv | 4 | 6 |
| Install Python | 3 | 6 |
| Install pinned R for the native binary policy test | 21.5 | 6 |
| Cache official Qt rcc package | 11 | 6 |
| Run Windows quick checks | 183 | 6 |
| Upload strict typing transcript | 1 | 6 |
| Prune uv cache | 1 | 6 |
| Post Cache official Qt rcc package | 0 | 6 |
| Post Install uv | 0 | 6 |
| Post Check out repository | 3 | 6 |
| Complete job | 0 | 6 |

| Cache step | Hits | Misses |
| --- | ---: | ---: |
| uv | 5 | 1 |
| Actions cache | 6 | 0 |
| Install uv | 1 | 0 |
| Cache official Qt rcc package | 1 | 0 |

## Deterministic code-health baseline and gates

| Step | Median (s) | Samples |
| --- | ---: | ---: |
| **Job** | 67 | 7 |
| Runner queue | 2 | 7 |
| Set up job | 1 | 7 |
| Run actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 | 18 | 7 |
| Fetch pre-squash baseline | 0 | 7 |
| Run astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b | 2 | 7 |
| Run uv python install | 1 | 7 |
| Run uv sync --frozen --only-group dev --no-install-project | 1 | 7 |
| Cache fixed code-health baseline | 1 | 7 |
| Resolve comparison base | 0 | 7 |
| Enforce shared code-health gates | 35 | 7 |
| Run actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 | 1 | 7 |
| Post Cache fixed code-health baseline | 0 | 7 |
| Post Run astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b | 0 | 7 |
| Post Run actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 | 0 | 7 |
| Complete job | 0 | 7 |

| Cache step | Hits | Misses |
| --- | ---: | ---: |
| uv | 5 | 1 |
| Actions cache | 5 | 1 |
| Run astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b | 1 | 0 |
| Cache fixed code-health baseline | 1 | 0 |

## Required Linux x64 Package Qualification / RCMetaStudio Linux x86_64

| Step | Median (s) | Samples |
| --- | ---: | ---: |
| **Job** | 380.5 | 2 |
| Runner queue | 3 | 2 |
| Set up job | 2.5 | 2 |
| Run actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 | 28 | 2 |
| Run astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b | 2.5 | 2 |
| Run uv python install | 1 | 2 |
| Install Linux package build and qualification libraries | 33.5 | 2 |
| Build and qualify the portable Linux package | 304.5 | 2 |
| Upload package and qualification evidence | 4.5 | 2 |
| Post Run astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b | 0 | 2 |
| Post Run actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 | 0 | 2 |
| Complete job | 0 | 2 |

| Cache step | Hits | Misses |
| --- | ---: | ---: |
| uv | 2 | 0 |

## Compile and package setup phases

RCMetaR is pure R. Its source install byte-compiles R and builds its package database. PyInstaller bundles existing binaries. Linux source-contrib transport delivers Posit binaries, with binary tags verified by the installer. The rpy2 native build remains in scope for the worker migration.

| Job | Phase | Median seconds | Samples |
| --- | --- | ---: | ---: |
| Native Qt6 Remaining Surfaces | editable app wheel | 3.2 | 8 |
| Native Qt6 Vertical Slice | editable app wheel | 3.2 | 8 |
| Quick Verification | editable app wheel | 3.3 | 7 |
| Required Linux x64 Package Qualification / RCMetaStudio Linux x86_64 | Linux binary R library install | 107.7 | 2 |
| Required Linux x64 Package Qualification / RCMetaStudio Linux x86_64 | RCMetaR R installation | 9.3 | 2 |
| Required Linux x64 Package Qualification / RCMetaStudio Linux x86_64 | editable app wheel | 1.7 | 2 |
| Required Linux x64 Package Qualification / RCMetaStudio Linux x86_64 | rpy2 native wheel | 5.4 | 2 |
| Required Windows Full R Stack Evidence (1) | RCMetaR R installation | 12.5 | 8 |
| Required Windows Full R Stack Evidence (1) | RCMetaR source archive | 1.0 | 8 |
| Required Windows Full R Stack Evidence (1) | editable app wheel | 3.2 | 8 |
| Required Windows Full R Stack Evidence (1) | third-party R closure install | 25.6 | 8 |
| Required Windows Full R Stack Evidence (2) | RCMetaR R installation | 11.9 | 8 |
| Required Windows Full R Stack Evidence (2) | RCMetaR source archive | 0.9 | 8 |
| Required Windows Full R Stack Evidence (2) | editable app wheel | 3.3 | 8 |
| Required Windows Full R Stack Evidence (2) | third-party R closure install | 23.8 | 8 |
| Required Windows Full R Stack Evidence (3) | RCMetaR R installation | 13.0 | 8 |
| Required Windows Full R Stack Evidence (3) | RCMetaR source archive | 1.0 | 8 |
| Required Windows Full R Stack Evidence (3) | editable app wheel | 3.2 | 8 |
| Required Windows Full R Stack Evidence (3) | third-party R closure install | 24.3 | 8 |
| Required Windows Full R Stack Evidence (checks) | RCMetaR R installation | 12.5 | 8 |
| Required Windows Full R Stack Evidence (checks) | RCMetaR source archive | 1.0 | 8 |
| Required Windows Full R Stack Evidence (checks) | editable app wheel | 3.2 | 8 |
| Required Windows Full R Stack Evidence (checks) | third-party R closure install | 24.7 | 8 |
| Required Windows x64 Package Qualification / RCMetaStudio Windows x64 | RCMetaR R installation | 12.3 | 8 |
| Required Windows x64 Package Qualification / RCMetaStudio Windows x64 | Windows wheel, R install and proof | 28.9 | 8 |
| Required Windows x64 Package Qualification / RCMetaStudio Windows x64 | editable app wheel | 3.1 | 8 |
| Required Windows x64 Package Qualification / RCMetaStudio Windows x64 | rpy2 native wheel | 21.5 | 8 |
| Source and Platform Verification (linux-x64) | editable app wheel | 1.5 | 8 |
| Source and Platform Verification (linux-x64) | rpy2 native wheel | 1.6 | 1 |
| Source and Platform Verification (windows-x64) | editable app wheel | 3.2 | 8 |

## Desktop shard balancing

The previous warm workflow's three Windows JUnit artifacts cover 153 passing
desktop scenarios. Their summed testcase times were 1482.8, 1087.3 and
941.6 seconds and their test wall times were 497.4, 366.1 and 316.7 seconds.
The existing partitioner assigned almost identical forecast totals to those
unequal shards. Refreshing its weights from the JUnit testcase times makes
the new assignments sum to about 1171 observed testcase seconds each.
These sums are scheduling weights for parallel workers. CI wall time remains
a separate measurement.

Get the three inputs from actions run 45026563658, attempt 2, artifact
names full-r-stack-windows-1-evidence, full-r-stack-windows-2-evidence and
full-r-stack-windows-3-evidence. The input within each artifact is
desktop-results.xml. Apply its passing parametrized testcase times to the
existing desktop partitioner and retain the rest of the duration config.
