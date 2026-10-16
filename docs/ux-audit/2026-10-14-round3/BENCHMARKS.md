# Verification resource changes

The TIFF converter now keeps one packed native raster instead of RGBA double
arrays, alpha/channel intermediates and a second RGB array. It uses the existing
pinned `png` decoder and real TIFF device on every platform. Output remains full
size, 600 dpi, white-backed and LZW-compressed.

[TIFF-BENCHMARK.json](TIFF-BENCHMARK.json) retains five alternating fresh-process
runs per implementation, exact commands, timings, peak RSS, failures and profile.
The input is the real HR subgroup [SVG](TIFF-input.svg), 6,298 × 10,800 pixels at
600 dpi. All ten exports completed and independently decoded.

| Actual work on this Linux host | Before | After |
| --- | --- | --- |
| Median export time | 51.371 s | 9.007 s |
| Time range | 50.028–53.639 s | 8.982–9.096 s |
| Median peak process RSS | 5.643 GiB | 1.199 GiB |
| Peak RSS range | 5.600–5.659 GiB | 1.199–1.200 GiB |

Export time excludes R startup and independent TIFF decoding. Peak RSS includes
both. Other heavy verification jobs were stopped; user desktop programs continued
running. Pixel comparison overlapped part of the first pair. The separate profile
is excluded from the measurements: array transposition, clipping and RGB
conversion dominate the old path. These measurements establish the improvement
for this input/host, not every machine or figure.

[TIFF-PIXELS.json](TIFF-PIXELS.json) compares all 68,018,400 pixels in bounded
strips. Dimensions, DPI and compression match. The maximum difference is **one
8-bit RGB level**, due to compositing/rounding; pixel identity is not claimed.
The existing transparency/white-margin/device gate passed all 43 checks.
Complete HR and IRR editor drives, each with 24 decoded exports, passed in
108 and 120 seconds within the original 600-second budgets. The subgroup editor
passed in 41 seconds within its original 240-second budget. Earlier incomplete
timeouts are not used as speedup measurements.

Run `bash docs/ux-audit/2026-10-14-round3/BENCHMARK.sh` to repeat the alternating
exports and pixel comparison. When its raw RDS is unavailable, the script
reconstructs the old function from `f68562f` in a private R environment. It does
not install old source or modify a qualified package.

The full profile no longer traverses the desktop registry twice. The complete
98-case pytest lane remains mandatory, with doctor and public authorities run
after it. Desktop cases use up to three resource-bounded offscreen workers, each with a
fresh Qt/R process. Native driving remains serial. Available RAM/CPU and Linux
cgroup limits bound concurrency; one CPU and 1 GiB remain reserved for the host. Original
120/240/600-second limits and numerical checks remain in force.

The 300-case review gallery retains all canonical SVGs, fits, styles and data
scenarios alongside bounded PNG previews: 144 dpi, at most 2,400 pixels on the
longest edge. Real publication-export drives still check full 600 dpi rasters.
The first bounded gallery completed in 178 seconds; the earlier publication
gallery took 3,489 seconds with different concurrent work. These observations
are not a controlled gallery benchmark. Full decoding and SVG parsing check
every case; no manifest error is accepted.

Corner-pixel checks convert one pixel instead of the full image. Contact-sheet
metrics avoid full white/difference canvases; thumbnails resize before RGB
conversion. [CONTACT-METRICS.json](CONTACT-METRICS.json) compares old and new
metric dictionaries on every retained native screenshot and a blank image:
exact equality. Full image decoding remains required.

The later DX pass (`273bd6a`, planned in `b77e0f4`) removes the remaining blanket
serialization for offscreen children and adds validated evidence reuse. The six
real-scenario pilot passed in 118.97 seconds, including the complete HR editor
exports and subgroup exports. This is a single observed pilot, not a controlled
speedup measurement. A CPU-affinity-constrained real E2E run selected one worker
and passed, establishing the low-capacity fallback on this Linux host.

[DX-RESUME.json](DX-RESUME.json) retains five unchanged-evidence validations and
real reruns after corrupt/missing PNGs, changed source and changed R startup
configuration. An intentionally missing forms root failed and was not cached.
All expected cases passed their assertions. Each unchanged case took roughly
0.27 seconds to validate; that excludes the one-time source/runtime signature
calculation. No Qt/R execution is claimed for a reused case: its original
manifest, observed results and artifact hashes remain the evidence. Runtime
fingerprints include executable namespace metadata; only RCMetaR's installation
metadata containing its temporary build path/date is omitted. Failed evidence
never becomes a cache entry. Source edits invalidate conservatively, and
`--fresh` disables reuse.

The final fresh desktop matrix passed all 98 cases in 1,213.68 seconds, versus
1,936.99 seconds for the earlier serial run. The entire final fresh profile took
1,835.012 seconds. This is an observed pair with different load/cache state, not
a repeated controlled speedup measurement. The complete warm desktop matrix,
including runtime signature and a fresh doctor, passed in **35.438 seconds**.
DX-WARM-PROFILE independently verifies that all 98 reused manifests/artifact hashes
are the original full-profile evidence.

The exact R-stack installation is retained for warm driving because another
installation changes compiled build-path bytes. Both original native and retained
full-source provenance are recorded; no executable-byte comparison is weakened.
The package library remains test-owned.
