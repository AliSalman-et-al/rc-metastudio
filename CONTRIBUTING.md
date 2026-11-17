# Contributing to RC MetaStudio

The best way to contribute is a [detailed issue](https://github.com/AliSalman-et-al/rc-metastudio/issues/new): tell us what you ran into or what you would like to do, and we will take it from there.

- **Found a bug or have an idea?** [Open an issue](https://github.com/AliSalman-et-al/rc-metastudio/issues/new), and see [Write an issue we can build from](#write-an-issue-we-can-build-from) for what helps.
- **Question or setup help?** Ask in [GitHub Issues](https://github.com/AliSalman-et-al/rc-metastudio/issues).
- **Need a statistical method or help understanding a result?** Include the effect measure, method settings and a small public or synthetic example. A methodological reference or direct R comparison helps, but is not required to ask.

## Why issues come first

Reviewing an outside pull request takes us longer than building the same change from a clear issue. We have to read code written without our context, check its statistical and data-handling implications, and usually rework it to fit the codebase. A good issue costs you less time, and we build, test and review the change in our normal process.

## Write an issue we can build from

Open an issue and include the information below. The issues we can act on fastest:

- **Start with the problem, not the solution.** Say what you were doing, what happened, and why it matters to you.
- **For a bug,** tell us what you did, what you expected and what you saw instead. Add the fewest steps that show it, ideally in a new project; how often it happens; whether it worked in an earlier version; your version, platform and install method; and the full error text or logs, pasted as text. **Help > About RCMS… > Copy debug info** provides runtime information.
- **For a feature,** describe the situation you are in and what you are trying to get done, how you handle it today, and what you would see if it worked.
- **One problem per issue.** Separate problems are easier to track and fix.
- **Anything else that helps is welcome,** such as code you suspect or your own ideas. None of it is required.

Issues are public. Share public or synthetic data and remove identifying information from projects and debug output.

We read every issue, and a clear one gives us something concrete to investigate. When a fix ships, the issue and linked changes provide the record.

## How credit works

Issue authors are credited on the issue itself, which stays linked to the problem they found. Filing an issue does not require a Contributor License Agreement. Earlier code contributions keep their existing attribution.

## Development setup

From a fresh clone:

```shell
uv sync --locked
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
```

Follow [Maintaining RC MetaStudio](docs/maintaining.md) to configure the real R runtime and library before running the application or its analysis workflows. Packaged releases include their runtimes; a source checkout needs the development setup.

### Toolchain

The repository uses Python 3.14 and uv. `pyproject.toml` and `uv.lock` define the Python environment. The [R dependency manifest](config/r-dependencies.json) defines the R runtime and package versions. Generated Qt modules belong in the build directory; edit the `.ui` form sources instead.

Use the locked environment and manifest-pinned R packages. Statistical calculations belong to those packages; changes must preserve their numerical results and expose their warnings. The [verification guide](.agents/skills/verify-rcms/SKILL.md) explains the required lanes and evidence.

## Common commands

```shell
uv run python scripts/verify.py smoke
uv run python scripts/verify.py fast
uv run python scripts/verify.py r-stack
uv run python scripts/verify.py pre-push
```

Run relevant checks while developing. Strict Windows typing precedes GUI qualification. Run `pre-push` after committing so its code-health check measures the committed revision. R-boundary and statistical changes also require the full real-R and desktop lane; see [Testing and verification](docs/testing.md).

## Code comments

Prefer clear names, types and straightforward code. Keep comments for non-obvious reasons, constraints and upstream behavior. Remove stale explanations when behavior changes. [AGENTS.md](AGENTS.md) contains the shared engineering rules.

## Pull requests

We build every change ourselves, from issues. If you have spotted something, the most helpful thing you can do is [open an issue](https://github.com/AliSalman-et-al/rc-metastudio/issues/new) describing it.

## License

Contributions incorporated into RC MetaStudio must use its [GNU General Public License v3.0 or later](LICENSE), `GPL-3.0-or-later`. Preserve existing third-party attribution.

Adapted from [OpenKnowledge's contribution guidelines](https://github.com/inkeep/open-knowledge/blob/main/CONTRIBUTING.md), also licensed under GPL-3.0-or-later.
