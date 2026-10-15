"""Editorial evidence routes; these identify relevant proof, not automatic closure."""
GROUPS=[
('L01 L02 L03 L04 L05 L06 H01 X01 RG04','DESIGN.json','Native wizard/import/help/validation inventory'),
('G01 G03 G06 G07 N08 N11 F06 E02','SELECTED-calculator-grid-precision.json','Actual input edits and save/reopen'),
('G02 D02 N10 F07 R5-09','SELECTED-project-display-labels.json','Ten-family live labels and selectors'),
('G04 G05 G08 M04 N09 F15','SHELL.json','Workspace navigation and structure dialogs'),
('M01 M02 M03 A04 F13 F14','SHELL.json','Opened native menus and recovery/eligibility'),
('S01 RG02 D01 A03','DESIGN.json','Result navigation/zoom and dialog sizing'),
('D03 R02 R11 R13 R14','SELECTED-project-reviewer-groups.json','Actual unnamed/named arms and reopened context'),
('D04 D05 R19 R5-07','SELECTED-project-round6-polish.json','Eligibility and invalid-contour recovery'),
('R01 R12 F16 R5-02 RG01 RG03','SELECTED-project-round6-polish.json','Live report overview and structured tables'),
('R03 R17 R5-04','SELECTED-audit-round3-round5.json','Dense 65-study upper/lower figures in all styles'),
('R04 R05 N03 R3-01','SELECTED-project-axis-sequential.json','Sequential reference/scale paths'),
('R06 R07 N07 R2-01','MATRIX-hr.json','HR cumulative and omission identities'),
('R08 N04 N05 F03 R5-01','SELECTED-project-reviewer-predictions.json','Sequential/subgroup clinical and fitted scales'),
('R09 F11 R5-11 R3-02','SELECTED-audit-round3-bubble-metrics.json','Metric-specific bubbles and guide bounds'),
('R10','SELECTED-project-reviewer-predictions.json','Single-arm natural-scale null/interval presentation'),
('R15 R16 N02 F04 R5-03 R5-05','SELECTED-project-round6-polish.json','Diagnostic coefficients at two/six digits; Tables/copy/CSV'),
('R18 F10','MATRIX-irr.json','IRR raw exposure, totals and subgroup identities'),
('E01 F08 N01 F09 R5-06','EXPORT-EVIDENCE.json','Retained actual vectors and long-heading defects'),
('X02','OPTIONS.json','Covariate and analysis setup empty-state controls'),
('A01 A02','DESIGN.json','Named controls, contrast samples; bounded accessibility scope'),
('A05','GUARD-KEYBOARD.json','Loaded-project keyboard/report/dirty-guard task'),
('N06 R2-02 R2-03','OUTCOMES.json','Maintained report/Tables copy/export assertions and manifest paths'),
('F01 F02 F05','OUTCOMES.json','Fixed/clinical-null authority and rendered presentation scenarios'),
('F12','DESIGN.json','Structured results navigation and component identities'),
('R5-08','OPTIONS.json','Subgroup setup/editor shared-layout wording'),
('R5-10','SELECTED-calculator-ratio-precision.json','Exact HR/IRR modes and post-reopen authority fit'),
]
def routes(rows):
 result={}
 for ids,path,label in GROUPS:
  for id in ids.split():
   assert id not in result,id
   result[id]={'path':path,'label':label}
 assert set(result)=={r['id'] for r in rows},set(r['id'] for r in rows)-set(result)
 return result
