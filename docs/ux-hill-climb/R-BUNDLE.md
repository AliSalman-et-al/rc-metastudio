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
Add RCMetaR/metafor/meta/mada and tiff (existing packaging requirement).
Keep 87 packages; remove 81 installed packages, plus the non-package translations
folder. Full closure: `base, base64enc, bit, bit64, boot, cli, clipr, compiler, CompQuadForm, cpp11, crayon, datasets, digest, dplyr, ellipse, farver, generics, ggplot2, glue, graphics, grDevices, grid, gtable, hms, isoband, jsonlite, labeling, lattice, lifecycle, lme4, mada, magrittr, MASS, mathjaxr, Matrix, meta, metabook, metadat, metafor, methods, minqa, mixmeta, mvmeta, mvtnorm, nlme, nloptr, numDeriv, parallel, pbapply, pillar, pkgconfig, png, prettyunits, progress, purrr, R6, rbibutils, RCMetaR, RColorBrewer, Rcpp, RcppEigen, Rdpack, readr, reformulas, rlang, rsvg, S7, scales, splines, stats, stringi, stringr, svglite, systemfonts, textshaping, tibble, tidyselect, tiff, tools, tzdb, utf8, utils, vctrs, viridisLite, vroom, withr, xml2`.

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
