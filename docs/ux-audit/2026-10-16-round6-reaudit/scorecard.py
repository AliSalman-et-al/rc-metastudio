"""Retain every prior ID; comparative statuses are editorial, not inferred tests."""
import json,collections
from pathlib import Path
HERE=Path(__file__).resolve().parent
old=json.loads((HERE.parent/'2026-10-16-round5-reaudit/SCORECARD.json').read_text())['rows']
changes={
'G02':('improved','Built-in TX Mean/menu identity repaired in ten-family label sweep; investigator names preserved. General terminology polish remains.'),
'G07':('improved','Calculator exact entry/provenance and live derived summaries repaired; dense layouts remain.'),
'D02':('improved','Contextual metric labels improved; some general method-family descriptions still need translation.'),
'D04':('fixed','Invalid contour input is inline, stops busy state, stays editable and recovers to real output.'),
'R01':('improved','Readable package-owned labels and reduced duplicate identity; remaining report hierarchy is coherent.'),
'R03':('improved','Long-figure caps and wrapped arm headers repaired; long outputs still require deliberate zoom/scroll.'),
'R08':('fixed','Structured subgroup results now identify fitted SE scales alongside natural-scale effects.'),
'R09':('fixed','Bubble legend entries/samples follow visible regression/CI/PI components; panel-bounded guides retained.'),
'R12':('improved','Duplicate default metric/type captions removed; investigator context retained.'),
'R15':('improved','Diagnostic coefficient precision and readable logit/OR interval headings finish the shared table surfaces.'),
'R16':('improved','Reference/moderator identities retained with selected precision and readable coefficient headings.'),
'R17':('fixed','Dense Default/subgroup CI caps now follow row spacing; prior long-forest regression closed.'),
'E01':('improved','Decoded exports preserve axes, colours, semantic legends and corrected header spacing.'),
'E02':('improved','Raw calculator/grid input integrity repaired through undo and save/reopen; existing dirty guards retained.'),
'A02':('improved','Sampled normal/selection contrast and non-colour cues; universal high-contrast qualification remains open.'),
'A03':('improved','Readable growing figures retain bounded caps; actual OS scaling/platform limits remain.'),
'RG01':('improved','Diagnostic overview and coefficient tables have readable selected-precision clinical/fitted scale identity.'),
'N02':('improved','Diagnostic moderator tables now honour precision and label logit/OR intervals; arbitrary long labels remain unqualified.'),
'N04':('fixed','Subgroup structured report retains tests and explicitly identifies SE scale.'),
'N08':('improved','Calculator exact input, derived preview and persistence improve; historical Windows-width trigger remains unqualified.'),
'N10':('improved','Built-in internal menu/report vocabulary repaired; minor case/method-family wording remains.'),
'N11':('improved','Round-trip-safe numeric editors preserve leading precision; arbitrary long values can still need horizontal scrolling.'),
'F04':('improved','Diagnostic selected precision and tiny numeric entry repaired while retaining genuine small effects; no universal formatting claim.'),
'F06':('improved','Raw precision/provenance and live derived summaries repaired; calculator layout remains dense.'),
'F07':('improved','Readable internal labels and Default style name repaired; case consistency and action-labelled dirty prompts remain polish.'),
}
rows=[]
for row in old:
 id=row['id'];status,note=changes.get(id,('unchanged',row['observation']))
 # Stale already-fixed baseline issues must not be carried into current observations.
 if id=='G05':note='Intervention/Control defaults, optional wizard names and preserved investigator/legacy names retained.'
 if id=='R19':note='Existing small-study cautions/eligibility retained; corrected contour recovery is tracked under D04/R5-07.'
 rows.append({'id':id,'verdict':status,'observation':note,'evidence':'OUTCOMES.json; INSPECTIONS.md; report coverage map'})
fixes={
'01':'Sequential/subgroup SE headings explicitly identify fitted scale; funnel SE axes do likewise.',
'02':'Default duplicate type/metric captions and Group: Group context removed; investigator text preserved.',
'03':'Diagnostic coefficients/ML tests honour two/six digits; logit/OR bounds explicit across Text/Tables/copy/export.',
'04':'Long standard/subgroup CI caps bounded by row spacing in all three styles.',
'05':'Package-owned Intercept/Moderator/Statistic labels are readable; internal keys remain internal.',
'06':'BMJ measured unequal wrapped headers improve; longest RevMan header overlaps caption/device top (R6-03), so not fully closed.',
'07':'Eligibility explains usable study count and invalid contours recover inline without stuck progress.',
'08':'Subgroup setup/editor explicitly explain shared layout with journal accents.',
'09':'Attached menus/calculators/reports use contextual readable metrics; no built-in TX Mean prefix.',
'10':'Tiny/huge/decimal/exponent input survives real editing, Accept, undo/save/reopen and independent post-reopen fit.',
'11':'Legend entries and samples follow actual regression/CI/PI visibility in display/export.'}
for num,note in fixes.items():rows.append({'id':'R5-'+num,'verdict':'improved' if num=='06' else 'fixed','observation':note,'evidence':'OUTCOMES.json; INSPECTIONS.md; round-six acceptance table in REPORT.md'})
rows.append({'id':'F16','verdict':'unchanged','observation':'Historical report-hierarchy finding omitted from the round-five scorecard, restored here. Calmer hierarchy retained; diagnostic overviews still need scrolling and retain multiple headings. No new round-six closure claimed.','evidence':'project-round6-polish report screenshots; INSPECTIONS.md'})
assert len(rows)==100 and len({r['id'] for r in rows})==100
out={'baseline':'../2026-10-16-round5-reaudit/REPORT.md','status':'DRAFT: statuses require final completed evidence review','counts':dict(collections.Counter(r['verdict'] for r in rows)),'rows':rows}
(HERE/'SCORECARD.json').write_text(json.dumps(out,indent=2)+'\n');print(out['counts'])
