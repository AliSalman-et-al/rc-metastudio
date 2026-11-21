# RC MetaStudio

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23118556.svg)](https://doi.org/10.5281/zenodo.23118556)

<img src="src/rc_metastudio/images/RC_MetaStudio_Logo_4K_Preview.png" alt="RC MetaStudio logo" width="560">

RC MetaStudio is free, open-source desktop software for meta-analysis. Enter study data in a spreadsheet-style table, choose an analysis, and inspect its estimates, plots and written report without writing code.

It is designed for researchers who want a graphical workflow for routine pooling and more detailed analyses, including subgroup analysis, meta-regression and diagnostic test accuracy. Supported meta-analytic models are fitted by the established R packages [metafor](https://www.metafor-project.org/), [meta](https://github.com/guido-s/meta) and [mada](https://cran.r-project.org/package=mada).

## Download and start

Download the appropriate archive from [GitHub Releases](https://github.com/AliSalman-et-al/rc-metastudio/releases/latest). Packaged releases include the required runtimes; you do not need a separate Python or R installation.

| Platform | Package | Start the application |
| --- | --- | --- |
| Windows x64 | `RCMetaStudio-windows-x64.zip` | Extract the archive and run `RCMetaStudio.exe`. |
| Apple silicon macOS | `RCMetaStudio-macos-arm64.dmg` | Open the disk image, drag RC MetaStudio to Applications, and launch it there. |
| Ubuntu 24.04 x86_64 | `RCMetaStudio-linux-x64.tar.gz` | Extract the archive and run `RCMetaStudio-linux-x64/LaunchRCMetaStudio.sh`. |

The macOS release process includes signing and notarization. Windows and Linux archives are unsigned. Other Linux distributions and Intel Macs are outside the current release qualification policy. See the release notes and [release guide](docs/release.md) for artifact checksums and platform details.

Start with **New project** to enter data, **Import data** for CSV, Excel or RevMan `.rm5` files, or **Open project** to continue a saved `.rcms` file. A project can contain independent outcome sheets.

Follow [Your first meta-analysis](docs/tutorials/first-analysis.md) to open a published example, run a model and export its output. The nine bundled projects use published data and cover binary, continuous, diagnostic, reported-effect, hazard-ratio and incidence-rate-ratio analyses. [Sample projects and sources](sample_projects/README.md)

## Analyses and output

- Enter raw study data or reported effect estimates with their uncertainty. Supported data include one-arm and two-arm binary and continuous outcomes, diagnostic counts and estimates, hazard ratios, and incidence rate ratios.
- Run standard, cumulative, leave-one-out, subgroup and meta-regression analyses where supported by the data and selected method.
- Fit joint sensitivity and specificity using the Reitsma bivariate model, with SROC plots and diagnostic meta-regression.
- Examine small-study effects through the **Publication Bias** menu. Available tests and plots depend on the effect measure and required inputs. Asymmetry does not by itself establish publication bias.
- Edit forest, funnel, bubble and SROC plots where applicable. Export plots as PDF, SVG, PNG or TIFF, and written reports as PDF or Word documents.
- Save study data in local `.rcms` projects. Export reports, plots and numerical values separately.

RC MetaStudio preserves the selected R package's estimators, inference and numerical results. Method availability, package warnings and model configuration remain visible in the workflow and output. The [dependency manifest](config/r-dependencies.json) records the pinned versions, and the [statistical authority decision](docs/adr/0001-delegate-statistical-decisions-to-authority-packages.md) explains this boundary.

## Documentation

- [Documentation index](docs/README.md).
- [Sample projects and their sources](sample_projects/README.md).
- [Hazard-ratio and incidence-rate-ratio workflows](docs/hr-irr.md).
- [Terminology and interpretation](CONTEXT.md).
- [Project file format](docs/project-format.md).
- [Development setup and maintenance](docs/maintaining.md).
- [Testing and verification](docs/testing.md).

## Feedback and contributions

Feedback and reproducible issues are the primary way to contribute. Use [GitHub Issues](https://github.com/AliSalman-et-al/rc-metastudio/issues) for bugs, questions and feature requests. Tell us what you were trying to do, what happened, and what you expected.

We build, test and review changes from these reports. [CONTRIBUTING.md](CONTRIBUTING.md) explains what helps us reproduce a problem and how to request a statistical method.

## Cite RC MetaStudio

> Salman A, Fatima K, Khan MS, Siddiqi TJ, Usman MS. RC MetaStudio: open-source desktop software for meta-analysis. Zenodo. https://doi.org/10.5281/zenodo.23118556

The [concept DOI](https://doi.org/10.5281/zenodo.23118556) identifies the software across releases. Cite the version used in your research; version-specific DOIs are available from the Zenodo record. Machine-readable metadata are in [CITATION.cff](CITATION.cff).

## License and origins

RC MetaStudio is developed and maintained by Research Consultancy. It is an independently maintained rewrite of OpenMeta[Analyst], whose authors and institutions retain attribution for their original work.

RC MetaStudio is distributed under GPL-3.0-or-later, where permitted by the original GPL-2.0-or-later grant covering derived portions. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md) for licensing, attribution and the affiliation disclaimer.
