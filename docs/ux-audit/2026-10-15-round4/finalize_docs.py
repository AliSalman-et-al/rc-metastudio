"""Write the final handoff only after aggregate and numerical receipts pass."""
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
full = json.loads((HERE/'FULL-PROFILE.json').read_text())
num = json.loads((HERE/'NUMERICAL-EQUIVALENCE.json').read_text())
assert full['passed'] and num['passed'] and num['original_field_count'] == 415 and num['max_absolute_difference'] == 0
source_revision = subprocess.check_output(['git','log','-1','--format=%h','--','src','r'],cwd=ROOT,text=True).strip()
review = (HERE/'REVIEW1-CHANGES.md').read_text()
review = review.replace('Final aggregate qualification is\npending until the final TESTS/FULL-PROFILE receipts are written.',
    f"Final aggregate qualification passed: {full['desktop_scenarios']} fresh desktop scenarios, doctor, current-source R gates, independent authorities and strict goldens. All 415 original numerical fields remain exact.")
(HERE/'REVIEW1-CHANGES.md').write_text(review)
original = subprocess.check_output(['git','show','c1f4cb2:docs/ux-audit/2026-10-15-round4/CHANGES.md'], cwd=ROOT,text=True)
rows = ['| Item | Implementation commits | Existing real Qt/R proof and artifacts |','| --- | --- | --- |']
for line in original.splitlines():
    if line.startswith('| ') and not line.startswith(('| Item ', '| ---')):
        rows.append('| ' + ' | '.join(cell.strip() for cell in line.split('|')[1:4]) + ' |')
(HERE/'CHANGES.md').write_text(review + '\n## Earlier round-four changes retained\n\n' + '\n'.join(rows) + '\n\nThe original native receipts remain in OBSERVATIONS/SCREENSHOTS. Review 1 repairs and current-source aggregate proof above supersede their historical unfinished status. The exact original numeric fields, tolerances and exceptions remain unchanged.\n')
(HERE/'README.md').write_text(f'''# Round 4 / Opus review 1 — implementation and proof

Implementation and qualification are complete on `ux/audit-improvements`, with
application source through `{source_revision}`. Every continuation commit was fast-forward
pushed; no PR or history rewrite. The user recovered the earlier `ca6815c` push.
STOP/INTERRUPTION receipts preserve that history.

Start with the [native before/after contact sheet](contact-sheet.html), then
[CHANGES](CHANGES.md) for each finding/design item and commit, [PLAN](PLAN.md) for
the pre-implementation choices, and [TESTS](TESTS.md) for exact commands, exits
and failures verbatim. [COMMITS](COMMITS.md) lists source and evidence commits.

The four review findings and D4-04..07 cover a native main-window start page,
clear dataset navigation, consistent native controls, a result-first report with
coherent sidebar/export behavior, and publication figure headers/ticks/footers.
There are no new statistical features.

Qualification: **{full['desktop_scenarios']} fresh desktop scenarios plus doctor**;
R package `Status: OK`, retained statistical/rendering checks, independent
public-package authorities, live bridge and strict golden gates. **415 original
numerical fields exactly unchanged**, maximum difference 0. Only reviewed
presentation text was refreshed through the sanctioned tool; see
[the text review](REVIEW1-GOLDEN-TEXT.md). Numerical contracts, tolerances and
exceptions remain fixed. The retained GUI selection passed 186 checks with one
Linux platform skip; changed production Python files passed configured typing.

[FULL-PROFILE](FULL-PROFILE.json) verifies each expected scenario and every retained
artifact hash. [NUMERICAL-EQUIVALENCE](NUMERICAL-EQUIVALENCE.json) contains every
original field. [REVIEW1-NATIVE](REVIEW1-NATIVE.json) binds fresh xcb commands,
R 4.6.1 identities, manifest hashes, inputs, observations and unmodified captures.
[INSTALLED-SOURCE](INSTALLED-SOURCE.json) binds the exact source and test-owned R
library. Authority packages and system libraries were not modified.
[REVIEW1-EXPORTS](REVIEW1-EXPORTS.json) binds actual four-format publication bytes
and clearly marked derived previews. [VISUAL-REVIEW](VISUAL-REVIEW.md) identifies
frames actually inspected, including rejected development frames.

[REPRODUCE](REPRODUCE.sh) uses the pinned runtime, owned-library installer, actual
Qt/R driver and existing numerical oracle. Raw logs and complete desktop outputs
remain ignored under raw/ and artifacts/verification; curated receipts and
screenshots are committed.

Opus acceptance and the independent native re-audit are subsequent review steps.
Linux source/controlled-fixture proof does not qualify native OS pickers,
keyboard-only/screen-reader access, OS DPI, other platforms or release packaging.
Historical development screenshots are retained without claiming blanket visual
approval; final representative native inspection is recorded separately.
''')
old = subprocess.check_output(['git','show','c1f4cb2:docs/ux-audit/2026-10-15-round4/VISUAL-REVIEW.md'],cwd=ROOT,text=True)
(HERE/'VISUAL-REVIEW.md').write_text('# Round 4 / review 1 — visual qualification\n\nCurrent inspection is recorded in [REVIEW1-VISUAL](REVIEW1-VISUAL.md). The self-contained [contact sheet](contact-sheet.html) compares bound native before/after captures. Final frames cover every changed presentation family; SVG geometry, public-package numerical comparisons and four-format export decoding are separate proof in REVIEW1-NATIVE/EXPORTS. Original SCREENSHOTS and rejected development frames remain historical evidence, without a claim that all historical captures are approved.\n\n## Historical interrupted-session review\n\nThe following describes the earlier stopped session; its pending work/status is superseded by README, TESTS and the current inspection log above.\n\n'+old)
p=ROOT/'docs/ux-audit/HANDOFF.md'
head=p.read_text().split('## Round four implementation — stopped at required push')[0]
p.write_text(head+f'''## Round four / Opus review 1 — ready for review

Application source is complete through `{source_revision}` on `ux/audit-improvements`.
All continuation commits were immediately fast-forward pushed; no PR. The user
recovered the earlier `ca6815c` push before continuation. Original failure and
interruption receipts remain in the [round-four folder](2026-10-15-round4/README.md).

The four review findings and ranked D4-04..07 are implemented: qualified BMJ
3/6-digit/export clearance; measured multiline headers and round transformed
ticks; concise actual-null wording; compact confidence/inference presentation;
a native start page with full/missing recent paths; clearer dataset navigation;
shared native control sizing/icons; result-first report reading and synchronized
sidebar/export actions; publication finishing. CHANGES maps commits and proof.
The [contact sheet](2026-10-15-round4/contact-sheet.html) gives before/after native
comparisons. REVIEW1-VISUAL records actual inspections.

Final `verify_all.py --full --fresh` passed {full['desktop_scenarios']} desktop
scenarios plus doctor, R package Status OK, independent authorities/live bridge
and strict goldens. All 415 original numerical fields are exact, maximum
difference 0; no numeric contract/tolerance/exception was changed. Reviewed golden
text only used the sanctioned presentation tool. Retained GUI checks: 186 passed,
one Linux platform skip; changed production Python typing passed. Exact commands,
all failures verbatim and hash-bound artifacts are in TESTS/TEST-RUNS/FULL-PROFILE.
Pinned R 4.6.1 and the test-owned library were used, with installed-source proof.

Next: Opus acceptance review, then the requested independent low-effort native
re-audit. Neither was started by the implementation agent. Accessibility,
OS DPI/file pickers, other platforms and release packages remain unqualified;
no all-option-combinations claim. Preserve the broadened design mandate and the
process rules above for subsequent rounds.
''')
print('Final README, CHANGES, VISUAL-REVIEW and HANDOFF written from passing receipts.')
