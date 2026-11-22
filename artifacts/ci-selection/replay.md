# CI selection replay

The latest 12 merged PRs are #607–#618. #606 is included to cover the requested range.

The replay uses the final changed paths from `gh api --paginate repos/AliSalman-et-al/rc-metastudio/pulls/<number>/files`, including old names for renames. Each row applies the ready-for-review policy to that complete diff. Historical attempts may have had a smaller diff.

For failure history, `gh api` listed pull-request workflow runs on each head branch between PR creation and merge, plus push runs at each merge SHA. The replay read every retained job attempt with `actions/runs/<id>/jobs?filter=all`. It counts failed and timed-out jobs, with aggregate failures identified in the evidence below. The branch/date filter scopes the check to Actions records for these PRs.

Quick, code health, classifier and aggregate gate are implicit in every selection. **Full** means both native Qt jobs, all three source targets, R checks and all three desktop shards, and all three package builds plus the macOS packaging contracts.

| PR | Heavy selection | Actions runs read | Failed jobs in selected lanes |
| --- | --- | ---: | ---: |
| [#606](https://github.com/AliSalman-et-al/rc-metastudio/pull/606) | Full | 4 | 0 |
| [#607](https://github.com/AliSalman-et-al/rc-metastudio/pull/607) | Full | 4 | 0 |
| [#608](https://github.com/AliSalman-et-al/rc-metastudio/pull/608) | Full | 6 | 1/1 |
| [#609](https://github.com/AliSalman-et-al/rc-metastudio/pull/609) | Full | 4 | 0 |
| [#610](https://github.com/AliSalman-et-al/rc-metastudio/pull/610) | Full | 14 | 19/19 |
| [#611](https://github.com/AliSalman-et-al/rc-metastudio/pull/611) | Full | 4 | 0 |
| [#612](https://github.com/AliSalman-et-al/rc-metastudio/pull/612) | Quick stage only | 4 | 1/1 |
| [#613](https://github.com/AliSalman-et-al/rc-metastudio/pull/613) | Both native Qt, all source targets, R checks and all desktop shards | 4 | 0 |
| [#614](https://github.com/AliSalman-et-al/rc-metastudio/pull/614) | Full | 6 | 3/3 |
| [#615](https://github.com/AliSalman-et-al/rc-metastudio/pull/615) | Full | 4 | 0 |
| [#616](https://github.com/AliSalman-et-al/rc-metastudio/pull/616) | Full | 6 | 2/2 |
| [#617](https://github.com/AliSalman-et-al/rc-metastudio/pull/617) | Full | 3 | 1/1 |
| [#618](https://github.com/AliSalman-et-al/rc-metastudio/pull/618) | Full | 3 | 0 |

**Result:** 27 of 27 failed job records were in selected lanes, including 18 underlying job failures and 9 aggregate failures. #606 adds no failure records.

The #612 and #617 master runs were cancelled during newer pushes, and their aggregate jobs recorded failures. #612's historical gate saw cancelled heavy dependencies. The current selector schedules only the quick stage for that docs-only diff. The replay includes the completed #618 master run.

## Failure records

- #608 · pull_request · [Deterministic code-health baseline and gates](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44466048268/job/135363966448) · selected
- #610 · pull_request · [Required Windows Full R Stack Evidence (2)](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44579494974/job/135756154427) · selected
- #610 · pull_request · [Required Windows Full R Stack Evidence (1)](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44579494974/job/135756154616) · selected
- #610 · pull_request · [Qt6 Integration Verification Gate](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44579494974/job/135765987576) · selected
- #610 · pull_request · [Required Windows Full R Stack Evidence (1)](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44574508738/job/135738528434) · selected
- #610 · pull_request · [Qt6 Integration Verification Gate](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44574508738/job/135749004369) · selected
- #610 · pull_request · [Required Windows Full R Stack Evidence (3)](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44566659989/job/135710379467) · selected
- #610 · pull_request · [Required Windows Full R Stack Evidence (1)](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44566659989/job/135710379515) · selected
- #610 · pull_request · [Required Windows x64 Package Qualification / RCMetaStudio Windows x64](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44566659989/job/135710379576) · selected
- #610 · pull_request · [Required Windows Full R Stack Evidence (2)](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44566659989/job/135710379586) · selected
- #610 · pull_request · [Qt6 Integration Verification Gate](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44566659989/job/135719027675) · selected
- #610 · pull_request · [Native Qt6 Vertical Slice](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44563837479/job/135701023277) · selected
- #610 · pull_request · [Required Windows Full R Stack Evidence (3)](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44563837479/job/135701023346) · selected
- #610 · pull_request · [Required Windows Full R Stack Evidence (1)](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44563837479/job/135701023394) · selected
- #610 · pull_request · [Required Windows Full R Stack Evidence (2)](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44563837479/job/135701023438) · selected
- #610 · pull_request · [Required Windows x64 Package Qualification / RCMetaStudio Windows x64](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44563837479/job/135701023474) · selected
- #610 · pull_request · [Qt6 Integration Verification Gate](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44563837479/job/135709925817) · selected
- #610 · pull_request · [Deterministic code-health baseline and gates](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44561653548/job/135692266001) · selected
- #610 · pull_request · [Native Qt6 Vertical Slice](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44561652920/job/135692575916) · selected
- #610 · pull_request · [Qt6 Integration Verification Gate](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44561652920/job/135700505735) · selected
- #612 · push · [Qt6 Integration Verification Gate](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44868950234/job/136739211188) · selected
- #614 · pull_request · [Native Qt6 Vertical Slice](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44938505474/job/136950399185) · selected
- #614 · pull_request · [Qt6 Integration Verification Gate](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44938505474/job/136953939068) · selected
- #614 · pull_request · [Deterministic code-health baseline and gates](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44938505465/job/136950362155) · selected
- #616 · pull_request · [Required Windows x64 Package Qualification / RCMetaStudio Windows x64](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44996938931/job/137129929915) · selected
- #616 · pull_request · [Qt6 Integration Verification Gate](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44996938931/job/137132502756) · selected
- #617 · push · [Qt6 Integration Verification Gate](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/45011213053/job/137174825398) · selected

## Expected Actions cost and first signal

These are modeled runner minutes per successful run, summed across parallel jobs before billing multipliers. The input is job start/end timestamps from [#617's staged PR run](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/45009729711). For targeted desktop jobs the estimate retains measured setup and R installation time and scales the pytest portion by the selected share of each shard's weights in `config/desktop-durations.json`. These are estimates for the listed single-file diffs with warm runners.

| Change | #617 ready PR | This PR, ready PR or master push | This PR, draft | #617 master push | First verification result, before → after |
| --- | ---: | ---: | ---: | ---: | --- |
| Docs only (`docs/maintaining.md`) | 4.4 min | 4.4 min | 4.4 min | 68.2 min | ~1.2 → ~1.2 min |
| Calculator copy (`src/rc_metastudio/forms/binary_back_calculation_dialog.ui`) | 68.2 min | 25.3 min | 22.2 min | 68.2 min | ~1.2 → ~1.2 min |
| R estimator (`r/RCMetaR/R/binary_methods.R`) | 68.2 min | 50.5 min | 47.3 min | 68.2 min | ~1.2 → ~1.2 min |

The first verification signal is code health at about 70 seconds in the reference run. The classifier returned in 10 seconds and Windows quick finished in 186 seconds. Both quick checks still start immediately after the workflow starts. Queue delays and cache misses vary. Changes to broad package and workflow inputs also run the new macOS and Linux package builds, so the example savings do not predict the nightly or full-run budget.
