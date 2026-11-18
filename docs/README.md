# RC MetaStudio documentation

Start with the [application README](../README.md) for downloads and supported workflows.

## Use the application

- [Your first meta-analysis](tutorials/first-analysis.md) walks through the BCG sample, model configuration, figure editing and exports, with a direct R reference calculation.
- [Sample projects](../sample_projects/README.md) provide ready-to-open data, source citations and provenance.
- [Hazard ratios and incidence rate ratios](hr-irr.md) explains data entry, source confidence, import and interpretation for these measures.
- [RevMan import](rm5-import.md) describes supported data, method mappings and differences to review before analysis.
- [Cumulative and leave-one-out analyses](cumulative-and-leave-one-out-design.md) explains cumulative sequences, leave-one-out ordering and report content.
- [Trial Sequential Analysis](trial-sequential-analysis.md) explains design settings, boundaries and report interpretation.
- [Terminology and interpretation](../CONTEXT.md) defines the concepts used in the interface and reports.
- [Project format](project-format.md) describes what an `.rcms` file contains and how older projects are read.
- [Contribution and support guidelines](../CONTRIBUTING.md) explains how to report a problem or suggest a change.

## Develop and maintain RC MetaStudio

- [Maintaining RC MetaStudio](maintaining.md) covers setup, source ownership, test commands and release preparation.
- [Testing and verification](testing.md) distinguishes statistical, desktop, native and packaged-release evidence.
- [Verification workflows](../.agents/skills/verify-rcms/SKILL.md) maps user behavior to executable proof and retained artifacts.
- [Release process](release.md) covers supported targets, candidate qualification and promotion.
- [File names and ownership](file-ownership.md) describes module responsibilities, relocation rules and public contracts.
- [Architecture decisions](adr/) explains significant trade-offs. [AGENTS.md](../AGENTS.md) gives the shared engineering rules.

## JOSS working draft

[paper.md](../paper.md) and its [bibliography](paper.bib) are a draft for author
review. Research-use evidence, author confirmations and the complete AI disclosure
remain open. The draft does not establish submission eligibility or a v1 release.

## Keep documentation current

Maintainers update the guide that owns a behavior when changing it. Tutorials
teach a complete workflow; task guides give operational steps; references state
formats and contracts; ADRs explain decisions. Link to the canonical instruction
instead of copying it into a new plan or audit report.

Track temporary plans and unresolved work in GitHub Issues. Git retains removed
investigations and dated run diaries. Retain a historical record in the working
tree only when it supplies unique provenance or an input still needed by a
maintained workflow, such as the [golden-reference records](ci/README.md).
