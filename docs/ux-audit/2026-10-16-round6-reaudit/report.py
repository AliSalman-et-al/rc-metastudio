"""Assemble the audit report from explicit editorial verdicts and retained evidence."""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
final='--final' in sys.argv
score=json.loads((HERE/'SCORECARD.json').read_text())
outcomes=json.loads((HERE/'OUTCOMES.json').read_text())
counts=score['counts']
head='# RC MetaStudio v0.5.0 — independent round-six native re-audit\n\n'
head+=('**Final verdict: do not merge this candidate until R6-03 is repaired.**' if final else '**IN PROGRESS. Current confirmed merge blocker: R6-03.**')
head+=''' The longest supported RevMan arm name overlaps the caption and crosses the figure-device top in native and exported SVG output. Numerical results are unchanged. This is a publication-output defect, not a failed statistical fit.

Round six is substantially better at preserving input, identifying scales and presenting results. PFT prediction limits use the natural proportion scale; Default intervals/markers/caps/arrows match the summary blue while study names remain black; internal metric labels and the retired Default suffix are removed on inspected paths. About and new saved-project metadata show 0.5.0. The remaining severe concern is output layout, not the repaired calculator path.

This audit started at **b48c802**, branch **ux/audit-improvements**. Only audit artifacts/scripts changed. Actual host/run timestamps are 15 October UTC (continuations may be later); the folder date follows the requested 16 October naming. All native drives use DISPLAY=:0/xcb, pinned R 4.6.1 and the test-owned retained library. [Provenance](PROVENANCE.json) checks all 80 RCMetaR source/install hashes. No system R library was changed.

'''
head+=f"Across **100 prior IDs: {counts.get('fixed',0)} fixed, {counts.get('improved',0)} improved, {counts.get('unchanged',0)} unchanged, {counts.get('regressed',0)} confirmed regressions**. This includes the 99 round-five IDs plus historical F16, accidentally omitted from that scorecard and restored here. Unchanged includes retained fixes and qualification gaps; improved does not imply universal closure. [Scorecard](SCORECARD.json).\n\n"
head+='''## Evidence and scope

[Exact command/exit/environment/log and manifest inventory](OUTCOMES.json),
[replay](REPLAY.md), [image inspection journal](INSPECTIONS.md),
[contact sheet](contact-sheet.html) and SELECTED-*.json bind the evidence.
Raw transcripts/owned inputs remain in ignored raw/ and under the helper's printed
artifacts/verification/rcms directory. A passing driver is not visual acceptance:
R6-03 was found in a driver that passes its narrower geometry assertions.

The independent authority sweep passes **91/91**. Strict golden replay passes;
all **415 original fields are exact**, maximum difference zero, with original
numerical contracts/tolerances/exceptions unchanged.
[Authorities](AUTHORITIES.json), [exact field comparison](NUMERICAL-EQUIVALENCE.json).

Linux source/native Qt proof does not qualify packaged Windows/macOS targets,
actual OS DPI, screen readers, every filesystem/dialect fault or an arbitrary
parameter/value Cartesian product. Control/choice inventories are distinguished
from executing every possible choice combination. Four-format export decoding
is distinguished from inspecting every exported pixel.

## Round-six acceptance review

| Area | Observation / evidence |
|---|---|
| Axes | Ratio log spacing/natural labels with opt-in linear; proportion and Sens/Spec natural 0–1; differences linear. Optional fitted transformations name their scale. Fresh geometry, exact fits/weights and persistence checks are in project-axis-* receipts/selected images; Apply has an additional targeted audit drive. |
| PFT PI | All three styles, standard/cumulative/omission/subgroup, Text/Tables/copy/export; public inverse agreement and subgroup-specific N. Seventeen pre-interruption completed cases retained, only missing BMJ subgroup replayed. |
| Default colours/style | Native project-reviewer-colours passes nine families/components and actual clipped arrows, four-format exports, black labels. Group/release drive visibly opens old-key Plots tab showing Default. |
| Groups/version | Unnamed spanners hidden; meaningful Participants preserved. Mean entered-effect fixture carries identity in caption and has no raw-data spanner. About and saved/reopened application.version show 0.5.0. |
| Diagnostic output | Numeric/factor/multiple moderators at two/six digits, explicit logit/OR CI headers, actual Tables/copy/CSV agreement; public coefficients unchanged. |
| Long headers | Default/BMJ improve, but longest RevMan case fails full-device/caption clearance (R6-03). R5-06 remains improved. |
| Calculator data | Fresh maintained keyboard, raw/entered/reconstructed mode, grid/import/clipboard, undo/save/reopen and post-reopen authority checks; final status requires completed registry listed in OUTCOMES. |
| Legends/contours | Actual component visibility governs legend samples. Invalid contour inputs show inline errors, stop progress and retain editable/recoverable state. |

'''
findings=(HERE/'FINDINGS.md').read_text().split('\n',1)[1]
head+='## New findings\n'+findings+'\n\n## Every prior ID\n\n'
head+='Status is comparative to round five (F16 restored from round four). Detailed scope is bounded by the evidence map above and the inspection journal.\n\n| ID | Status | Observation | Evidence |\n|---|---|---|---|\n'
for r in score['rows']:
 head+=f"| {r['id']} | **{r['verdict']}** | {r['observation'].replace('|','/')} | [native receipts](OUTCOMES.json), [inspections](INSPECTIONS.md) |\n"
head+='''
## Changelog and further work

The current 0.5.0 entry accurately describes the observed input/scale/colour/report
improvements. Its broad wrapped-header wording needs the R6-03 qualification;
publication layout is not uniformly finished. The portable Ubuntu download and
TIFF performance statements belong to separate package/benchmark evidence; this
audit does not requalify those claims. Historical version strings in older records
are not current-runtime version defects.

Repair R6-03 first. Then add the missing semantic BMJ Events/Total heading,
give About a sensible screen-bounded preferred size, and round optional fitted
PLN ticks coherently. Existing opportunities remain: compact calculator layouts,
less package-taxonomy translation, sentence-case/action-labelled prompts,
full from-launch keyboard tasks, actual assistive-technology and OS-scale checks.
No new statistical procedure is needed.

RevMan/Cochrane patterns inform the recommendations: clear distinction between
fitted and reported scales, concise visible footnotes, explicit uncertainty
controls and useful raw-data headings. [Primary references](DESIGN-REFERENCES.md).

## Failures, interruptions and cleanup

The deliberate interruption orphaned one owned prediction child; only its recorded
PID was stopped. Seventeen complete cases survived and were reused. Resume failures
were audit harness import shadowing and a missing recorder namespace binding;
the exact failed/terminated logs remain raw. The final missing-case replay passed.
The numerical helper's output was relocated into this audit and its historical
file restored byte-exact; raw/NUMERICAL-RELOCATION.json records hashes.
No failed receipt is relabelled as passing. Final cleanup and completion counts
must be reconciled against OUTCOMES before acceptance.
'''
(HERE/'REPORT.md').write_text(head)
print('report rows',len(score['rows']),'final',final)
