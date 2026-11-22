# Contributing to RC MetaStudio

Use the issue tracker to report a bug, ask for help or propose a feature or statistical method.

## How to contribute or get help

All feedback and support go through [GitHub Issues](https://github.com/AliSalman-et-al/rc-metastudio/issues):

- **Report a bug:** [Open an issue](https://github.com/AliSalman-et-al/rc-metastudio/issues/new) describing what happened and how to reproduce it.
- **Request a feature or statistical method:** [Open an issue](https://github.com/AliSalman-et-al/rc-metastudio/issues/new) describing the review task you are trying to complete. For a statistical method, include the effect measure, model settings, and a small public or synthetic example; a methodological reference or direct R comparison is helpful but not required.
- **Ask a usage or installation question:** Open a question on [GitHub Issues](https://github.com/AliSalman-et-al/rc-metastudio/issues). Include your operating system, RC MetaStudio version, and whether you installed a packaged release or ran from source.

## Why changes are built from issues (pull request policy)

We do not accept unsolicited external pull requests; maintainers build, verify, and review changes directly from issues.


## How to write an issue we can act on

1. **Describe the problem before proposing a fix.** Explain what you were doing, what happened, and what you expected.
2. **Keep one problem per issue.** Separate issues are easier to reproduce, verify, and link to a release.
3. **For bugs, include reproduction details:**
   - Minimal steps to trigger the problem (ideally starting from a bundled sample project or a new project).
   - How often it occurs and whether it worked in an earlier version.
   - Runtime and platform details copied from **Help > About RCMS… > Copy debug info**.
   - Full error text pasted as text rather than screenshots alone.
4. **For features or statistical methods, include clinical/review context:**
   - What question or dataset shape you are analyzing and how you work around it today.
   - Expected inputs, outputs, and any reference package or paper if you have one.
5. **Protect participant and unpublished data.** GitHub Issues are public. Attach only public or synthetic datasets, and remove any identifying details from project files or pasted logs.

## Community expectations

RC MetaStudio is a scientific software project used by clinical researchers and methodologists. In all issue discussions and project spaces:

- Stay focused on the software, statistical methods, and reproducible evidence.
- Communicate respectfully and constructively, including when disagreeing on statistical defaults or design trade-offs.
- Do not post harassment, personal attacks, or confidential patient/participant data.

Maintainers may moderate or close comments that violate these expectations.

The project contact is listed in [NOTICE.md](NOTICE.md).

## Attribution and credit

Issue reporters are credited via the public issue linked to the fix and release notes. Opening an issue does not require a Contributor License Agreement. Earlier code contributors retain their existing attribution in Git history and source notices.

## Building from source and running tests

See [Maintaining RC MetaStudio](docs/maintaining.md) for source setup and verification.

## Licensing

Any material incorporated into RC MetaStudio is distributed under the project's [GNU General Public License v3.0 or later](LICENSE) (`GPL-3.0-or-later`), preserving all existing third-party attribution (see [NOTICE.md](NOTICE.md)).

---

*Issue-first contribution structure adapted from [OpenKnowledge's contribution guidelines](https://github.com/inkeep/open-knowledge/blob/main/CONTRIBUTING.md) (`GPL-3.0-or-later`).*
