# macOS packaging benchmark

[PR #622](https://github.com/AliSalman-et-al/rc-metastudio/pull/622) at
`bcef1ca2cc599a0de5cce9c47d6403a56a5601d2` runs the wheel-based package.
The earlier attempt on a different commit stopped because R staging imported
the project before editable installation. The corrected run and its full
rerun use the same commit and PR merge ref.

## Method

The baseline package jobs are runs 45013207688 and 45020115092. They requested
identical source Qt SDK and PyQt cache keys and each missed both. The earlier
run saved them under its PR merge ref. The default-branch SDK key was first
created at 12:43 UTC, after both jobs had started. This made the PR workflow
pay the cold build cost even with an existing cache mechanism. PyQt built
with one worker and Qt with three. The published wheels eliminate those
builds for the 14.4 PR profile.

The full workflow rerun was requested with `gh run rerun 45026563658`.
Job timings use the Actions jobs API. Build spans use timestamps in the
macOS job logs. Code health is the first substantive signal. The quick
result is the Windows gate that enables heavy jobs. Both use attempt start
as time zero. Full workflow wall time uses the Actions completed timestamp.

## Cold run

[Attempt 1](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/45026563658/attempts/1)
succeeded. It took 10m 27s for full macOS packaging and 16m overall.
It saved both the RCMetaR and package-specific uv caches. The official
rcc SDK cache hit. All 164 R dependencies installed as binaries.

| Baseline compile or install span | Baseline median | PR cold |
| --- | ---: | ---: |
| qtbase Ninja tasks | 11m 49s | 0s |
| qtsvg Ninja tasks | 22s | 0s |
| PyQt6 source-to-wheel | 34m 37s | 0s |
| Locked PR wheels plus editable app setup | — | 5s |
| Posit R binaries, policy and closure validation | 33s | 32s |
| RCMetaR source build, install and load | 16s | 17s |
| Staged R native API bridge install | 6s | 8s |
| Forms, resources and PyInstaller | 33s | 41s |
| ad-hoc signing and strict verification | 11s | 13s |
| Creation of the unsigned ZIP | 29s | 33s |
| Complete requalification of the extracted ZIP | 2m 26s | 3m 03s |

The package still stages and relocates official R, inspects and signs the
native payload, runs the packaged analysis and Cocoa checks, and repeats
qualification from the exact extracted ZIP. The cold run's analysis and
normal app-entry checks took about 2m 14s before ZIP creation. The PR
profile labels the resulting artifact `-pr-wheels`; the source Qt/PyQt
pipeline qualifies macOS 14.0 for release and nightly, and the trusted
release pipeline handles signing, notarization and the DMG.

## Reproduce the timing table

```powershell
gh api repos/AliSalman-et-al/rc-metastudio/actions/runs/45026563658/attempts/1
gh api 'repos/AliSalman-et-al/rc-metastudio/actions/runs/45026563658/attempts/1/jobs?per_page=100'
gh api repos/AliSalman-et-al/rc-metastudio/actions/runs/45026563658/attempts/2
gh api 'repos/AliSalman-et-al/rc-metastudio/actions/runs/45026563658/attempts/2/jobs?per_page=100'
gh run view 45026563658 --attempt 1 --log
gh run view 45026563658 --attempt 2 --log
```

## Warm rerun

[Attempt 2](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/45026563658/attempts/2)
restored the official Qt SDK, installed RCMetaR and package-specific uv
caches. The package passed in 8m 04s. The embedded binding stage installed the cached
wheel in under one second and logged no build. RCMetaR copy and load
verification took four seconds and logged no source install.

| Compile or install work | Before median | PR cold | PR warm |
| --- | ---: | ---: | ---: |
| qtbase Ninja tasks | 11m 49s | 0s | 0s |
| qtsvg Ninja tasks | 22s | 0s | 0s |
| PyQt6 native wheel compile | 34m 37s | 0s | 0s |
| Locked wheels and editable application setup | — | 5s | 3s |
| Posit binary R closure install and validation | 33s | 32s | 35s |
| RCMetaR install/load or restore/load | 16s | 17s | 4s |
| Staged-R bridge build/install or cached install | 6s | 8s | <1s |

The source/platform job kept its separate runner-R API build. The PR
package reused the bridge built against the package's private R framework.
Checkout in the corrected cold run took 4 seconds, compared to a median
51 seconds before. Runner queue wait was 4 seconds cold and 3–4 seconds
for the two baseline package runs.

The separate source/platform builds took 8.0s and 12.3s for the API wheel,
against a 9.5s baseline median. Its editable project wheel took 5.1s cold
and 9.1s warm, against a 4.4s baseline median. The focused macOS contracts
job performed no third-party source build.

## Before and after

| Metric | Baseline median | PR cold | PR warm | After median |
| --- | ---: | ---: | ---: | ---: |
| Code-health result | 1m 03s | 1m 23s | 1m 04s | 1m 14s |
| Quick gate | 4m 28s | 4m 15s | 3m 17s | 3m 46s |
| Full macOS package | 58m 01s | 10m 27s | 8m 04s | 9m 16s |
| macOS source and platform | 2m 22s | 2m 18s | 2m 11s | 2m 14s |
| Focused macOS contracts | 52s | 1m 31s | 54s | 1m 12s |
| Whole PR workflow | 62m 39s | 16m 00s | 14m 36s | 15m 18s |

Both workflow attempts passed. Windows package qualification finished last
among the heavy jobs in the cold attempt. Warm package evidence verifies
macOS arm64, deployment floor 14.4, Qt/PyQt 6.12.0, R 4.6.2 and provenance
for the exact PR merge commit `896b0f019f0a69c27c4b8ac9a0d1cf3096c8a9cc`.
