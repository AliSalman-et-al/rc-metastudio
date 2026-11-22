# RC MetaStudio

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23118556.svg)](https://doi.org/10.5281/zenodo.23118556)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPL--3.0--or--later-blue.svg)](LICENSE)

<img src="src/rc_metastudio/images/RC_MetaStudio_Logo_4K_Preview.png" alt="RC MetaStudio logo" width="560">

RC MetaStudio is free, open-source desktop software for quantitative evidence synthesis and meta-analysis. Researchers enter study data into spreadsheet-style outcome sheets, choose an effect measure and statistical model from menus, and inspect tables, editable figures, and formatted reports without writing code.

## Why RC MetaStudio exists

Systematic reviewers often work with several outcomes and may need models that are only available through statistical code. RC MetaStudio gives each outcome its own data and model settings. Reviewers can fit those models in the desktop app and trace the fitted method back to its R package.

## Download and install

Download the archive for your platform from [GitHub Releases](https://github.com/AliSalman-et-al/rc-metastudio/releases/latest). Each package bundles its own Python, Qt 6, and R (`4.6.2`) runtimes and pinned R packages; you do not need to install Python or R separately.

| Platform | Release asset | How to start |
| --- | --- | --- |
| Windows x64 | `RCMetaStudio-windows-x64.zip` | Extract the archive and run `RCMetaStudio.exe`. |
| Apple silicon macOS (macOS 14+) | `RCMetaStudio-macos-arm64.dmg` | Open the disk image, drag **RC MetaStudio** to **Applications**, and launch it from there. |
| Ubuntu 24.04 x86_64 | `RCMetaStudio-linux-x64.tar.gz` | Extract the archive and run `RCMetaStudio-linux-x64/LaunchRCMetaStudio.sh`. |

- The normal macOS release uses Developer ID signing, Apple notarization and stapling. Windows and Linux archives are unsigned. Check the release notes for the trust profile, `SHA256SUMS` and per-platform CycloneDX SBOMs.
- **Platform scope:** Intel macOS and Linux distributions other than Ubuntu 24.04 x86_64 are outside the release qualification baseline (see [ADR-0009](docs/adr/0009-support-qualified-release-platforms.md) and [Releasing RC MetaStudio](docs/release.md)).

### Run from source

To run or test RC MetaStudio from a Git checkout, follow [Development setup in Maintaining RC MetaStudio](docs/maintaining.md#set-up-the-development-environment).

## Quick start

1. Launch RC MetaStudio.
2. Open one of the nine bundled published examples via **File > Open sample project** (or **Open a sample project** on the Welcome page before you have recent files). Saving a sample opens **Save as…** so the bundled copy stays intact.
3. Follow [Your first meta-analysis](docs/tutorials/first-analysis.md) to run a random-effects risk-ratio analysis on the bundled BCG vaccine trial dataset (`Binary - BCG vaccine and tuberculosis, Colditz 1994`), inspect the pooled estimate (`RR 0.49, 95% CI 0.34 to 0.70`), edit and export the forest plot and written report, and optionally check the exact numbers against a direct `metafor` R script ([`bcg-reference.R`](docs/tutorials/bcg-reference.R)).

To start with your own data, choose **New project**, **Import data** (CSV, Excel `.xlsx`, or RevMan 5 `.rm5`), or **Open project** (`.rcms`). A single project can hold multiple independent outcome sheets.

## Supported data, analyses, and outputs

Enter one- or two-arm binary and continuous outcomes, diagnostic accuracy counts, reported effects, hazard ratios, or incidence rate ratios. Use the study calculators to reconstruct effects from reported statistics. The Analysis menu offers fixed-effect and random-effects pooling, cumulative and leave-one-out analyses, subgroup analysis, meta-regression, small-study effects and trial sequential analysis where eligible.

You can edit figures and export PDF, SVG, PNG or TIFF. Export the written report to PDF or Word, or export formatted tables and unrounded results as CSV. See the [user guide](docs/user-guide.md) for workflows and analysis options.

## Statistical foundation and transparency

RC MetaStudio delegates statistical estimation and inference to established, version-pinned R packages:

- **[metafor](https://www.metafor-project.org/)** (`5.2-1`): univariate pooling, heterogeneity estimators, inference, cumulative, leave-one-out, subgroup, meta-regression, and forest/bubble/funnel geometry.
- **[meta](https://github.com/guido-s/meta)** (`8.5-0`): classical small-study asymmetry tests, Deeks' test, and trim-and-fill sensitivity analyses.
- **[mada](https://cran.r-project.org/package=mada)** (`0.5.12`): count-based Reitsma bivariate diagnostic models, SROC curves, prediction regions, and diagnostic meta-regression.
- **[gsDesign](https://cran.r-project.org/package=gsDesign)** (`3.11.0`): Lan–DeMets alpha- and beta-spending boundaries for Trial Sequential Analysis (see [ADR-0011](docs/adr/0011-implement-trial-sequential-analysis-over-metafor-and-gsdesign.md) for the explicit authority exception covering TSA-specific formulas).

Every pinned version is recorded in [`config/r-dependencies.json`](config/r-dependencies.json),. See [ADR-0001](docs/adr/0001-delegate-statistical-decisions-to-authority-packages.md).

## Automated tests

The suite covers project I/O, Qt workflows, numerical regression, real R integration and packaging. Run `uv run python scripts/verify.py fast` from a configured checkout. Follow the [verification guide](docs/maintaining.md#verification-lanes-and-test-suites) for setup and full desktop checks.

## Documentation

- [Your first meta-analysis](docs/tutorials/first-analysis.md): guided walkthrough with R reference verification.
- [User guide](docs/user-guide.md): data entry, calculators, CSV/Excel/RevMan import, analyses, figures, and exports.
- [Trial Sequential Analysis guide](docs/trial-sequential-analysis.md): TSA settings, plots, and CTU comparison.
- [Sample projects and sources](sample_projects/README.md): all nine bundled datasets and their citations.
- [Terminology and interpretation](CONTEXT.md): domain glossary used across the interface and reports.
- [Project file format](docs/project-format.md): `.rcms` v3 archive structure, validation, and migrations.
- [Contributing and support](CONTRIBUTING.md): reporting bugs, requesting methods, and community guidelines.
- [Maintaining RC MetaStudio](docs/maintaining.md): source setup, R configuration, verification lanes, and architecture.
- [Documentation index](docs/README.md): full map including architecture decisions (`docs/adr/`) and release process (`docs/release.md`).

## Feedback, support, and contributing

Use [GitHub Issues](https://github.com/AliSalman-et-al/rc-metastudio/issues) to report bugs, ask usage questions, or request statistical methods and features. Maintainers build, test and review changes from reproducible issues. See [CONTRIBUTING.md](CONTRIBUTING.md) for what to include (including **Help > About RCMS… > Copy debug info**), community expectations, and licensing.

## Cite RC MetaStudio

You can copy a formatted citation or export BibTeX, RIS, or EndNote directly from **Help > Cite…** inside the application.

> Salman A, Fatima K, Khan MS, Siddiqi TJ, Usman MS. RC MetaStudio: open-source desktop software for meta-analysis. Zenodo. https://doi.org/10.5281/zenodo.23118556

Use the version-specific DOI from the Zenodo record for the release you used. Machine-readable citation metadata are in [CITATION.cff](CITATION.cff).

> `[PLACEHOLDER: Authors to confirm final author list, affiliations, and ORCIDs in CITATION.cff and .zenodo.json before JOSS submission, and add the JOSS paper citation/DOI once published.]`

## License and origins

RC MetaStudio is developed and maintained by Research Consultancy (RC). It is an independently maintained rewrite of OpenMeta[Analyst], whose original authors and institutions retain attribution for their work and are not affiliated with or endorsing RC MetaStudio.

RC MetaStudio is distributed under the GNU General Public License v3.0 or later (`GPL-3.0-or-later`), where permitted by the original `GPL-2.0-or-later` grant covering derived portions. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md) for full licensing, attribution, and disclaimers.
