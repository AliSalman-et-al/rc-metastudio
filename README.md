# RC MetaStudio

<img src="src/rc_metastudio/images/RC_MetaStudio_Logo_4K_Preview.png" alt="RC MetaStudio logo" width="720">

RC MetaStudio is an open-source desktop application for performing and reviewing meta-analyses without writing code.

It supports standard, cumulative, leave-one-out, subgroup, meta-regression, and diagnostic analyses. You can inspect results, create forest and bubble plots, export plots as PDF, PNG, SVG, or TIFF, and save your work in an `.rcms` project.

## Research workflow

Start a new project, open a recent project, or import a CSV. CSV import lets you map columns, preview the resulting studies, and correct validation errors before replacing the current workspace. The study grid accepts direct edits and rectangular paste; deletion can be undone. Missing years and numeric cells remain missing instead of becoming invented values.

The workspace separates study data from results. Analysis setup identifies excluded or incomplete studies, keeps an unfinished draft when you return to the data, and lets you retry a failed run with its settings intact. Long-running analysis and figure work runs in a separate worker so the window remains responsive and can stop or close safely. After an unexpected exit, startup offers a validated recovery snapshot when one exists.

Each saved analysis keeps its input snapshot, study order, report, backend versions, and portable figures. Open a saved result without recomputing it, inspect missing-artifact states, or export a stored figure. Use **Edit a copy** to run the analysis with new settings. The original result stays available for comparison. Figure edits do not change its numerical result.

Diagnostic analyses retain univariate sensitivity, specificity, likelihood-ratio, and diagnostic-odds-ratio methods. Count-based joint sensitivity/specificity analyses use the `mada` 0.5.12 Reitsma bivariate model, with editable and exportable SROC confidence/prediction geometry. Additive continuous and categorical diagnostic meta-regression reports separate sensitivity and specificity coefficient plots.

## Small-study effects analysis

Choose **Publication Bias** after at least two included studies to open the guided small-study effects analysis. “Publication Bias” is the navigation label; the analysis reports associations between study size or precision and observed effects and does not provide a bias-present or bias-absent verdict. RCMetaR computes method-specific eligibility from the included study set and shows the exact reason when a procedure or required input is unavailable. Ordinary and contour-enhanced funnels are presentation artifacts that can be edited and regenerated from the saved run. Diagnostic odds ratios use the separate Deeks effective-sample-size funnel.

The workflow reports the package-native methods supported by `meta` 8.5-0 and the distinct mixed-effects Egger model from `metafor` 5.0-1. Depending on the effect measure and available raw inputs, it can show classical Egger, Harbord, Rücker AS+RE, Peters, Pustejovsky–Rodgers, Begg–Mazumdar, Deeks, trim-and-fill, and exploratory infinite-precision estimates. Each result includes its package/version and call; unavailable procedures retain their precise eligibility reason. Read the [small-study effects glossary](CONTEXT.md) for interpretation boundaries and the [release guide](docs/release.md) for runtime verification requirements.

## Download and install

Download a release from [GitHub Releases](https://github.com/AliSalman-et-al/rc-metastudio/releases). Releases built with the three-platform policy contain:

- Windows x64: `RCMetaStudio-windows-x64.zip`
- Apple silicon Mac: `RCMetaStudio-macos-arm64.dmg`
- Linux x86_64: `RCMetaStudio-linux-x64.tar.gz`

On Windows, extract the archive and run `RCMetaStudio.exe`.

On macOS, open the disk image, drag RC MetaStudio to Applications, and launch it from Applications. Trusted releases are Developer ID signed, notarized, and stapled. Community releases may be unsigned. Windows and Linux packages are unsigned.

The 0.5.0 support policy targets Windows 10 version 1809 or later on x64,
macOS 14 or later on Apple silicon, and Ubuntu 24.04 or 26.04 LTS on x86_64.
The Linux archive is built on Ubuntu 24.04 and includes a private R runtime.
Qualification for 0.5.0 is incomplete. Preliminary package journeys passed on
Ubuntu 24.04 and 26.04, but the final release candidate and expanded workflow
matrix still need qualification. See the [release guide](docs/release.md) for the
required evidence.
Other Linux distributions and architectures are outside this support policy.

On Ubuntu 24.04 x86_64, extract the archive and run
`RCMetaStudio-linux-x64/LaunchRCMetaStudio.sh`.

## Feedback

Report bugs and request improvements through [GitHub Issues](https://github.com/AliSalman-et-al/rc-metastudio/issues). Describe what happened, what you expected, and how to reproduce it. Do not attach private project data.

Public code contributions are not currently accepted. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Development

See [Maintaining RC MetaStudio](docs/maintaining.md) for setup, verification, and repository conventions. The [project format reference](docs/project-format.md) documents `.rcms` files, and the [release guide](docs/release.md) covers the build and promotion workflow.

## License and provenance

RC MetaStudio is developed by Research Consultancy (RC) and maintained by Ali Salman and RC MetaStudio contributors. It is derived from the original OpenMeta[Analyst] project.

The project is distributed under the GNU General Public License, version 3 or later, where permitted by the original GPL-2.0-or-later grant covering derived portions. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md) for the full terms, provenance, warranty, and affiliation disclaimer.
