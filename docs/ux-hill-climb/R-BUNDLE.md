# R bundle reduction

Linux baseline: HEAD 130a0c17, retained qualified output from BUNDLE.md.
Exact build command: `LIBRARY_PATH="$PWD/build/bundle-audit/linker" bash scripts/build-linux-package.sh --python-exe "$PWD/.venv/bin/python"`.
Linux extracts pinned Posit R 4.6.1, installs dated Noble binaries with
scripts/install-r-deps-linux.R, installs r/RCMetaR with R CMD INSTALL,
then copies R after building the rpy2 API bridge and PyInstaller executable.
Windows copies the selected runtime in Copy-RRuntime; macOS stages the official
R.framework and installs RCMetaR before signing. Neither host is available here.

Proof obligations before changes: extracted API bridge startup, package native
qualification (including real analysis), current-source R-stack where runnable.
Failures of interest: missing optional runtime packages, missing fonts/encodings
or runtime share resources, invalid native stripping, numerical drift. Keep share
(runtime encodings, fonts and licenses), package data and lazy-load databases.
Do not alter package versions. Strip only ELF debug sections with GNU strip.

Installed metadata closure uses scripts/r-bundle-closure.R and
Depends/Imports/LinkingTo recursively. rpy2.robjects startup was observed to load
compiler, graphics, tools, utils, grDevices, stats, datasets, methods, base.
Add RCMetaR/metafor/meta/mada and tiff (existing packaging requirement), and stats4 (dynamic summary dependency).
Keep 88 packages; remove 80 installed packages, plus the non-package translations
folder. Full closure: `base, base64enc, bit, bit64, boot, cli, clipr, compiler, CompQuadForm, cpp11, crayon, datasets, digest, dplyr, ellipse, farver, generics, ggplot2, glue, graphics, grDevices, grid, gtable, hms, isoband, jsonlite, labeling, lattice, lifecycle, lme4, mada, magrittr, MASS, mathjaxr, Matrix, meta, metabook, metadat, metafor, methods, minqa, mixmeta, mvmeta, mvtnorm, nlme, nloptr, numDeriv, parallel, pbapply, pillar, pkgconfig, png, prettyunits, progress, purrr, R6, rbibutils, RCMetaR, RColorBrewer, Rcpp, RcppEigen, Rdpack, readr, reformulas, rlang, rsvg, S7, scales, splines, stats, stats4, stringi, stringr, svglite, systemfonts, textshaping, tibble, tidyselect, tiff, tools, tzdb, utf8, utils, vctrs, viridisLite, vroom, withr, xml2`.

Baseline R logical bytes: 305263589; compressed tar.gz: 300882373.
Per-package baseline (logical bytes, largest first):

| Package | Bytes |
| --- | ---: |
| Matrix | 13509773 |
| ggplot2 | 12584781 |
| bslib | 11711149 |
| survival | 10236779 |
| RcppEigen | 9513528 |
| translations | 9314286 |
| mathjaxr | 7851980 |
| stringi | 7669464 |
| rmarkdown | 6853731 |
| stats | 6252689 |
| metafor | 5780482 |
| mgcv | 5195598 |
| lme4 | 4913964 |
| sass | 4857786 |
| data.table | 4748264 |
| base | 4047500 |
| colorspace | 4020216 |
| Rcpp | 4000516 |
| viridis | 3887650 |
| Hmisc | 3756976 |
| glmnet | 3614595 |
| grDevices | 3579021 |
| rbibutils | 3414890 |
| ape | 3406247 |
| testthat | 3369643 |
| tools | 3177968 |
| meta | 2984547 |
| nlme | 2876486 |
| vctrs | 2685836 |
| grid | 2583664 |
| farver | 2573806 |
| utils | 2563057 |
| jsonlite | 2422138 |
| dplyr | 2350604 |
| interp | 2350276 |
| jomo | 2328627 |
| tzdb | 2300375 |
| latticeExtra | 2262414 |
| methods | 2172320 |
| graphics | 2120717 |
| fontawesome | 2108744 |
| htmlwidgets | 2093302 |
| vroom | 2048525 |
| isoband | 2008701 |
| cli | 1951293 |
| rlang | 1930173 |
| broom | 1869176 |
| mvtnorm | 1799206 |
| tidyr | 1733034 |
| mice | 1699038 |
| lattice | 1684242 |
| quantreg | 1632871 |
| tibble | 1591694 |
| jquerylib | 1555038 |
| SparseM | 1554243 |
| systemfonts | 1533856 |
| ordinal | 1471221 |
| knitr | 1427713 |
| roxygen2 | 1406193 |
| MASS | 1390070 |
| readr | 1377623 |
| pillar | 1374022 |
| viridisLite | 1353190 |
| diffobj | 1352630 |
| RCMetaR | 1217911 |
| htmlTable | 1194044 |
| metadat | 1135215 |
| pan | 1097219 |
| checkmate | 1072523 |
| cpp11 | 1070003 |
| nloptr | 1044110 |
| scales | 1040024 |
| bit | 1034797 |
| rpart | 1014792 |
| haven | 906117 |
| cluster | 898908 |
| shape | 789228 |
| ps | 780012 |
| foreign | 775946 |
| gridExtra | 769333 |
| Rdpack | 747357 |
| xfun | 735767 |
| purrr | 729117 |
| bit64 | 721540 |
| boot | 709043 |
| mitml | 649807 |
| callr | 602245 |
| stringr | 598378 |
| S7 | 595341 |
| processx | 567061 |
| tcltk | 562010 |
| mada | 555923 |
| rstudioapi | 524704 |
| forcats | 517644 |
| irlba | 504142 |
| parallel | 500877 |
| MatrixModels | 476751 |
| brew | 472426 |
| utf8 | 459685 |
| mixmeta | 459579 |
| datasets | 456785 |
| xml2 | 448908 |
| svglite | 438389 |
| rsvg | 428481 |
| iterators | 424517 |
| textshaping | 415788 |
| digest | 415647 |
| htmltools | 404750 |
| commonmark | 389419 |
| magrittr | 376406 |
| desc | 373301 |
| tidyselect | 366306 |
| foreach | 359990 |
| fs | 357336 |
| otel | 340763 |
| mvmeta | 336934 |
| glue | 323981 |
| deldir | 320608 |
| withr | 311953 |
| gtable | 294313 |
| lifecycle | 268639 |
| yaml | 263269 |
| pkgload | 244000 |
| ellipse | 238762 |
| stats4 | 236629 |
| pkgbuild | 231154 |
| minqa | 229447 |
| spatial | 229255 |
| compiler | 222044 |
| Formula | 193433 |
| metabook | 192713 |
| rprojroot | 189366 |
| crayon | 184075 |
| nnet | 174279 |
| prettyunits | 169848 |
| tinytex | 159364 |
| waldo | 156345 |
| KernSmooth | 150745 |
| backports | 144014 |
| splines | 143178 |
| class | 133322 |
| hms | 125730 |
| numDeriv | 124869 |
| acepack | 122560 |
| progress | 121792 |
| reformulas | 121684 |
| fastmap | 117788 |
| evaluate | 117430 |
| pbapply | 110969 |
| R6 | 107754 |
| cachem | 100304 |
| generics | 99268 |
| codetools | 95709 |
| tiff | 79480 |
| clipr | 74329 |
| memoise | 67043 |
| rappdirs | 66887 |
| labeling | 66725 |
| CompQuadForm | 66405 |
| png | 64019 |
| highr | 62513 |
| brio | 62414 |
| mime | 62273 |
| ucminf | 59033 |
| RColorBrewer | 58352 |
| jpeg | 50134 |
| base64enc | 45972 |
| pkgconfig | 28835 |
| praise | 23367 |

Package directory totals overlap the per-package totals:

- help: 45,060,437 bytes
- html: 2,695,601 bytes
- doc: 62,473,644 bytes
- demo: 0 bytes
- tests: 0 bytes
- include: 12,083,978 bytes
- po: 2,835,755 bytes

R top-level components:

- bin: 424,145 bytes
- library: 277,361,814 bytes
- etc: 11,209 bytes
- share: 1,160,752 bytes
- doc: 10,808,147 bytes
- SVN-REVISION: 46 bytes
- modules: 1,339,328 bytes
- include: 419,881 bytes
- lib: 13,720,256 bytes
- COPYING: 18,011 bytes

Measurement script and JSON: artifacts/verification/r-bundle/. Evidence is local.
Tcl/Tk package: 562,010 bytes; linked host Tk is separately bundled by Linux.
Base/recommended priority and debug-section measurements will be retained with final evidence.

Priority totals (installed metadata): {'base': 28618459, 'recommended': 39074947, 'NA': 200354122} bytes.
Baseline ELF .debug sections: 29,564,382 bytes (size -A); per-binary
measurements in debug.json. Other ELF sections are retained.
Excluded package directories including translations: 82, totaling 123211433 bytes.

## Qualification and correction

First reduction build exited 0, including native extracted qualification, and
91 independent authority comparisons passed. Broader bridge checks then found
stats4 missing when formatting Reitsma meta-regression summaries (2 failures);
a third failure required the source-only pkgload loader. Added stats4 as an
explicit runtime root and rebuilt. The declared metadata closure alone is not
sufficient: the final 88-package set includes this observed dynamic dependency.
The initial 82 excluded directories/123,211,433 bytes above become 81 directories
(80 installed packages plus translations)/122,974,804 bytes with stats4 retained.

Retained-package documentation/build headers plus R doc/include: 88,401,246
baseline bytes before restoring stats4. Runtime share (1,160,752 bytes) stays;
so do package data, R lazy-load databases, NAMESPACE, DESCRIPTION, metadata and
translations belonging to retained packages. No statistical source/version edit.
Linux-only GNU strip --strip-debug preserves dynamic symbols. Windows/macOS
payload exclusions were not changed: their native layouts/signing/provenance
need host qualification. Windows ZIP Fastest -> Optimal is unbuilt; macOS uses
ditto ZIP unchanged (no DMG generated by this script). Linux gzip default -> -9.

The full `uv run python scripts/verify.py r-stack` is not run on the reduced
runtime: it installs test/development dependencies and checks source RCMetaR,
which would replace the artifact under test. Use the existing compatible bridge
subset against extracted R, and retain its command/environment in checks.sh.
Two source-loader cases requiring pkgload are excluded, not claimed as passing.
The independent analysis_authorities.R copy changes only its loader from
pkgload::load_all to library(RCMetaR); all 91 comparisons remain unchanged.

## Final Linux result

| Component | Before bytes | After bytes |
| --- | ---: | ---: |
| R logical | 305,263,589 | 66,769,599 |
| Whole bundle logical | 699,965,045 | 459,948,481 |
| tar.gz | 300,882,373 | 155,248,045 |

Download reduction: 145,634,328 bytes (48.4%). Windows ZIP, macOS ZIP/DMG:
not built (Linux host); no before/after values claimed.

Final closure: 88 packages, 80 installed packages removed plus translations.
Final checks use `bash artifacts/verification/r-bundle/checks.sh` with the exact
environment and inputs retained there. `Rscript packaged-authorities.R` exited 0:
91 unchanged numerical comparisons passed. `uv run python -m pytest tests/r_stack
-k 'not test_reitsma_release_values_match_public_mada_with_portable_tolerances and
not test_meta_regression_contract_matches_pinned_joint_model_and_ml_tests' -q`
exited 0: 7 passed, 2 deselected (the two source-loader cases).
The original failed subset log remains first-r-stack-subset.log; it is not a pass.

Final full build command above exited **0** at 2026-10-30 22:30 UTC.
Extracted native packaged-smoke.json reports passed=true, including real R
workflows and sample opens, with build-time R hidden. Exact command and inputs
are in build-linux-package.sh; final-qualification retains observations, logs,
runtime identity and native captures. This establishes the existing qualification
scenarios, not every possible analysis input or unbuilt platform.

All implementation commits were pushed fast-forward individually: 19604d6c,
0dfa985d, 7cb9b207, 23584563, 681f2bfc, c9ebf412. No push failure or retry.
Final evidence manifest hashes the retained local inputs, commands and outputs.

## Packaged-R QA

Earlier packaged-R QA evidence survives at `/tmp/rcms-qa-evidence/`:
11 `*-plot-workflow-*` runs, doctor (`20261030T223837Z-2115274e-doctor`),
and the reported 14 analysis scenarios all retain `stdout.log`, `runtime.json`,
`manifest.json`, steps and captures. Inspection also found a fifteenth analysis
run, `20261030T230903Z-88dd92fa-options-zero-cells`; all 27 saved stdout logs
contain `WORKFLOW PASSED`. These are October 30 observations, not freshly rerun
workflows. The 91 passed authority comparisons remain in
`/home/ali/Documents/Code/rc-metastudio/artifacts/verification/r-bundle/authorities.log`,
with `packaged-authorities.R`, `checks.sh` and `authorities.json` beside it.

The packaged `Rscript -e 'cat(commandArgs(TRUE))' a b` ignored both arguments;
the unreduced `build/ux-round3/r-home` launcher printed `a b`, and packaged
`R --vanilla -f` with `--args` also worked. The cause was relocation, not removed
packages: build-linux-package.sh replaced native Rscript with a shell wrapper
that passed expression arguments straight to R without the `--args` delimiter.
Its filename branch happened to insert the delimiter. Quoting was intact.

The relocation step now lives in `scripts/configure_linux_r_launchers.py` and
preserves upstream `Rscript` as `Rscript.real`, setting its `RHOME` override to
the runtime's current location. Upstream handles expression/file option parsing.
A copy of the reduced packaged runtime, with upstream launchers restored from
the original extracted archive, passed this exact build step in isolation.
`artifacts/verification/rscript-launcher/` retains reproduction/proof commands,
logs and RM5 CSV outputs: expression arguments print `a b`, quoted/empty arguments
survive, and `tests/e2e/rm5_reference.R` receives its input and two output paths
and produces both outcome estimates. Run the shell scripts from the repo root.
No original build files were modified. A full package rebuild and qualification
are still required to ship the corrected launcher; none was performed here.
