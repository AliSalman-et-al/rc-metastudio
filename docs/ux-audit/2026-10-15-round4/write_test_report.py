"""Retain exact attempted commands and failure text alongside the final receipts."""
import json
from html import escape
from pathlib import Path
import re
import shlex

HERE = Path(__file__).resolve().parent
records = json.loads((HERE / 'TEST-RUNS.json').read_text())
full = json.loads((HERE / 'FULL-PROFILE.json').read_text())
numerical = json.loads((HERE / 'NUMERICAL-EQUIVALENCE.json').read_text())
assert full['passed'] and numerical['exact_before_after'] and numerical['original_field_count'] == 415
lines = ['# Round 4 / Opus review 1 — verification', '',
    'Final current-source qualification passed. The full fresh profile covers '
    f"{full['desktop_scenarios']} desktop scenarios, doctor, the R package gates, strict golden compatibility, live bridge and independent authority comparisons. "
    'All 415 original numerical fields are exactly unchanged; maximum difference 0. '
    'See [FULL-PROFILE](FULL-PROFILE.json), [NUMERICAL-EQUIVALENCE](NUMERICAL-EQUIVALENCE.json), '
    '[installed source](INSTALLED-SOURCE.json), and [native receipts](REVIEW1-NATIVE.json).', '',
    'The retained GUI boundary selection passed 186 checks with one Linux platform skip; '
    'the changed production Python files passed the configured type check. The full fresh profile '
    'is the final aggregate gate. Native drives use pinned R 4.6.1 and the test-owned library; '
    'every source revision was reinstalled before driving. No numerical oracle or tolerance was refreshed. '
    'Only reviewed presentation text was refreshed with the sanctioned tool; see REVIEW1-GOLDEN-TEXT.md.', '',
    'Failures and interruptions below are retained development observations, not passing evidence. '
    'The first continuation full run was deliberately stopped after visual inspection found the wrong '
    'transformed-null variable. Its exact package-check failure remains in the recorded log; '
    'REVIEW1-FULL-INTERRUPTION.json names the owned process and signal. Two outer wrappers exited 143 '
    'with no sealed desktop manifest; REVIEW1-INTERRUPTIONS.json retains the cleanup/provenance. '
    'The earlier push exit 143 had empty stdout and stderr (STOP.json); the user recovered it before this continuation. '
    'Every continuation source/evidence commit was fast-forward pushed successfully.', '',
    'The unconfigured whole-repository type invocation reported `Found 178 diagnostics`; '
    'a scoped configured check identified six new errors, which were fixed before the changed-file check passed. '
    'The unavailable `ruff` executable and the initial unavailable bare `python` command are tool availability failures, '
    'not passing checks. No claim is made for whole-repository typing or linting.', '',
    'The documentation whitespace check exited 2 only for trailing spaces in the verbatim failed-child transcript. Those bytes are deliberately retained; the same check excluding that transcript passed.', '',
    '## Exact recorded commands and exits', '', '| Label | Exit | Exact command |', '| --- | ---: | --- |']
for row in records:
    command = escape(shlex.join(row['command']), quote=False).replace('|', '&#124;').replace('`', '&#96;').replace('\n', '&#10;')
    lines.append(f"| {row['label']} | {row['exit_code']} | <code>{command}</code> |")
lines += ['', 'Each runner receipt in [TEST-RUNS](TEST-RUNS.json) binds the exact argv, environment, revision, times and raw-log SHA. '
    'The full profile has its own three command receipts and hash-bound per-scenario manifests. '
    'Raw transcripts stay under ignored raw/ and artifacts/verification; curated failure lines are below.', '',
    '## Verbatim failed-attempt output', '']
for row in records:
    if not row['exit_code']:
        continue
    content = (HERE / 'raw' / row['log']).read_text(errors='replace')
    failure = [line for line in content.splitlines() if re.search(
        r'(?:\w*Error:|^AssertionError$|^StopIteration$|^KeyboardInterrupt|^\s+assert |^FAILED |^error(?:\[|:)|timed out after|^ERROR|^Status:|^Found \d+ diagnostics|^Failed;)', line)]
    if row['label'] == 'review1-verbatim-whitespace':
        failure = content.splitlines()
    if row['label'] == 'review1-full-qualified':
        failure += (HERE / 'REVIEW1-PACKAGE-INTERRUPTION.json').read_text().splitlines()
    if row['label'] == 'review1-full-final':
        failure += (HERE / 'REVIEW1-FULL-INTERRUPTION.json').read_text().splitlines()
    lines += [f"### {row['label']} (exit {row['exit_code']})", '', '```text',
              *(failure or ['[No matching diagnostic line; inspect the exact raw transcript bound by its SHA in TEST-RUNS.json.]']), '```', '']
lines += ['## Failed UX driver child (verbatim)', '', 'Maintained entry point: `uv run python scripts/verify_rcms.py ux-improvements` (offscreen within review1-full-fresh). The corrected native and offscreen gesture drives are recorded separately.', '', '```text', (HERE / 'REVIEW1-UX-DRIVER-FAILURES.txt').read_text(), '```', '', '## Failed reference child (verbatim)', '', 'Exact maintained entry point: `uv run python scripts/verify_rcms.py audit-round3-references` (offscreen, within review1-full-current). The failed child manifest is bound by REVIEW1-MATRIX-FAILURE.json.', '', '```text', (HERE / 'REVIEW1-MATRIX-FAILURES.txt').read_text(), '```', '', '## Completed R check failure (verbatim)', '', '```text', (HERE / 'REVIEW1-R-PACKAGE-FAILURES.txt').read_text(), '```', '', 'The earlier detailed package failure block is retained verbatim in [R-PRESENTATION-FAILURES](R-PRESENTATION-FAILURES.txt).', '',
    'Qualification limits: Linux source and controlled fixtures only. Native OS picker interaction, keyboard-only/screen-reader '
    'coverage, OS DPI, other platforms and release packaging remain unqualified. Opus acceptance and independent native re-audit are separate review steps.', '']
(HERE / 'TESTS.md').write_text('\n'.join(lines))
print(f'Wrote {len(records)} exact command receipts and all nonzero attempt diagnostics.')
