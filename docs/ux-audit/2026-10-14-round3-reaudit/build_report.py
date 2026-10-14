"""Build the baseline-ID ledger and native matrix without changing product code."""
from pathlib import Path
import re,json
HERE=Path(__file__).resolve().parent
baseline=(HERE.parent/'2026-10-14-reaudit/REPORT.md').read_text()
rows=re.findall(r'^\| ([A-Z]+\d+) \| \*\*(\w+)\*\* \| (.*?) \| (.*?) \|$',baseline,re.M)
assert len(rows)==68
changed={'R01':'improved','R02':'improved','R04':'improved','R05':'improved','R06':'improved','R07':'fixed','R08':'improved','R09':'improved','RG03':'fixed','N03':'improved','N06':'fixed','N07':'fixed','E01':'improved','N04':'improved'}
notes={
'E01':'Identity and table row structure are restored in copied/exported reports; native table CSV and decoded four-format exports pass.',
'N04':'Standard and subgroup tables gain consistent fitted heterogeneity fields and existing PI; legacy package printouts remain.',
'R01':'Subgroup and standard tables now carry more fitted fields; package printouts remain in other sections.',
'R02':'Copied/exported identity is restored and survives opening another project; standalone figure context remains incomplete.',
'R04':'Comparative sequential nulls and row precision now agree across observed views; standalone context and long-plot font size remain.',
'R05':'Zero-bound residue is removed and genuine 1e-10 effects survive; enormous Z statistics still use long fixed-point strings.',
'R06':'Study added (k) and study/year labels agree in figure and report; help still needs to distinguish sequence from display order.',
'R07':'HR/IRR omission names and estimate/CI rows agree; omission-only fits do not acquire an overall row.',
'R08':'Subgroup k, Q, df, P, I², applicable τ² and existing PI appear in report tables; residual package printout is still dense.',
'R09':'OR/PLO bubble ticks span the plotted range with round unpadded values; study identity and moderator units remain absent.',
'RG03':'Diagnostic workflow notes precede component blocks, each with its executed estimator; combined method counts pass.',
'N03':'Distinct full-range bubble ticks, row-relative precision, bounded null lines and collapsed-range guards now pass; the BMJ context label has a separate F08 limitation.',
'N06':'Copy and export retain executed identity and tab-separated headers/data rows; payloads match exactly.',
'N07':'The HR/IRR omission defect is closed; cumulative row roles and k agree across report and figure.',
'N01':'Coefficient/entered-effect headings remain correct in default/RevMan views; newly inspected BMJ axis says Mean (F08). No baseline BMJ comparison proves a new regression.',
'G01':'Fresh Linux grids are readable; the old Windows persisted category-width allocation was not reproduced on this host.',
'A05':'Maintained keyboard/copy/export paths execute; complete keyboard-only traversal and focus restoration remain unqualified.',
}
mapnames={
'L01':'shell-types','L02':'shell-launcher','L03':'shell-template-saved','L04':'shell-generic-metric','L05':'shell-empty-outcome','L06':'shell-template-native-picker',
'G01':'shell-grid','G02':'matrix-onearm-mean-standard-figure','G03':'shell-grid','G04':'shell-grid','G05':'helper-calculator-continuous','G06':'helper-calculator-diagnostic','G07':'helper-calculator-continuous','G08':'shell-add-covariate',
'M01':'menu-analysis','M02':'menu-file','M03':'shell-covariates','M04':'shell-structure','S01':'helper-ux-improvements-14',
'D01':'helper-calculator-continuous','D02':'helper-review-workflows-05','D03':'helper-review-workflows-08-0','D04':'helper-ux-improvements-04','D05':'helper-review-workflows-05',
'R01':'matrix-twoarm-mean-subgroup-report','R02':'matrix-hr-standard-report','R03':'matrix-hr-standard-figure','R04':'matrix-twoarm-mean-cumulative-figure','R05':'precision-00','R06':'matrix-hr-cumulative-report','R07':'matrix-hr-leave-one-out-figure','R08':'matrix-twoarm-mean-subgroup-report','R09':'precision-06','R10':'matrix-onearm-proportion-standard-report','R11':'matrix-onearm-mean-standard-figure','R12':'matrix-reg-coef-standard-figure','R13':'helper-review-workflows-05','R14':'matrix-twoarm-smd-standard-report','R15':'helper-analysis-diagnostic-joint','R16':'helper-analysis-diagnostic-regression-multiple','R17':'matrix-hr-standard-figure','R18':'matrix-irr-standard-figure','R19':'helper-small-study-effects',
'E01':'helper-ux-improvements','E02':'helper-ux-improvements','H01':'shell-quick-start','X01':'shell-grid','X02':'shell-covariates',
'A01':'helper-ux-improvements-13','A02':'shell-grid','A03':'helper-calculator-diagnostic','A04':'shell-covariates','A05':'menu-view',
'RG01':'helper-analysis-diagnostic-joint','RG02':'helper-ux-improvements-14','RG03':'matrix-diagnostic-cumulative-report','RG04':'shell-csv-entry',
'N01':'matrix-generic-effect-standard-figure','N02':'helper-analysis-diagnostic-regression-multiple','N03':'precision-06','N04':'helper-ux-improvements-13','N05':'matrix-twoarm-mean-subgroup-report','N06':'shell-exported-report-editor','N07':'matrix-irr-leave-one-out-report','N08':'helper-calculator-diagnostic','N09':'shell-covariates','N10':'shell-add-covariate','N11':'helper-calculator-diagnostic'}
def link(stem):
 exact=HERE/'screenshots'/(stem+'.png')
 files=[exact] if exact.exists() else sorted((HERE/'screenshots').glob(stem+'*.png'));assert files,stem
 p=files[0];return f'[{p.stem}](screenshots/{p.name})'
ledger=['| ID | Verdict vs 14 October | Current observation / remaining gap | Evidence |','|---|---|---|---|']
for id,old,note,evidence in rows:
 verdict=changed.get(id,'unchanged')
 if id not in notes:
  note=note.replace('now ','').replace('R2-02','resolved R2-02')
  note=f'Baseline {old} state retained: {note}'
 else:note=notes[id]
 ledger.append(f'| {id} | **{verdict}** | {note} | {link(mapnames[id])} |')
(HERE/'SCORECARD.md').write_text('\n'.join(ledger)+'\n')
from collections import Counter
print(Counter(changed.get(id,'unchanged') for id,_,_,_ in rows))
workflows=['standard','cumulative','leave-one-out','subgroup','meta-regression']
lines=['| Data type | Standard | Cumulative | Leave-one-out | Subgroup | Meta-regression |','|---|---|---|---|---|---|']
for family in ['onearm-proportion','onearm-mean','reg-coef','generic-effect','twoarm-proportion','twoarm-mean','twoarm-smd','diagnostic','hr','irr']:
 cells=[]
 for w in workflows:cells.append('N: '+link('matrix-'+family+'-'+w+'-figure.png'.removesuffix('.png'))+', '+link('matrix-'+family+'-'+w+'-report.png'.removesuffix('.png')))
 lines.append('| '+family+' | '+' | '.join(cells)+' |')
(HERE/'MATRIX.md').write_text('\n'.join(lines)+'\n')
