import hashlib,json,re
from pathlib import Path
from shutil import copy2
root=Path.cwd();h=root/'docs/ux-audit/2026-10-16-round5';rows=json.loads((h/'REVIEW1-CURATION.json').read_text());existing={r['destination'] for r in rows}
old=json.loads((h/'NATIVE.json').read_text());pairs=[]
def copy(source, label):
 target=h/'screenshots'/('review1-'+label+'-'+source.name)
 key=str(target.relative_to(root))
 copy2(source,target)
 entry=dict(source=str(source.relative_to(root)),destination=key,sha256=hashlib.sha256(source.read_bytes()).hexdigest(),purpose='Unmodified native caption/editor follow-up capture')
 if key in existing:
  next(row for row in rows if row['destination']==key).update(entry)
 else:
  rows.append(entry);existing.add(key)
 return 'screenshots/'+target.name
for family,before_label,filename in [('regression','native-caption-regression','04-0-matrix-results-figure.png'),('sroc','native-sroc-caption-after','05-0-matrix-results-figure.png'),('funnel','native-root-funnel','07-0-family-plot-reopened.png')]:
 attempts=[json.loads(p.read_text()) for p in (h/'raw').glob('review1-native-editor-'+family+'*.json')]
 passed=sorted((r for r in attempts if r['exit_code']==0),key=lambda r:r['finished'])
 if not passed:continue
 log=h/'raw'/passed[-1]['log']
 p=Path(re.search(r'Evidence: (.+)',log.read_text())[1])
 before=copy(root/old[before_label]['evidence']/filename,family+'-before')
 actions=list(map(json.loads,(p/'steps.jsonl').read_text().splitlines()))
 a=next(r for r in actions if r['action']==('family-plot-reopened' if family=='funnel' else 'review1-caption-initial'))
 after=copy(p/a['captures'][0],family+'-after')
 if family=='funnel':
  initial=next(r for r in actions if r['action']=='review1-caption-initial');copy(p/initial['captures'][0],family+'-initial')
 pairs.append(dict(title='Review 1 · '+family.title()+' caption',description=('Same edited caption, before/after readable size and spacing. Initial clinical context is retained separately; Apply/reopen/Cancel/removal and all four exports pass.' if family=='funnel' else 'Same source input; readable caption separates the identity lines. Bundled arm names are also corrected. Real edit/reopen/Cancel/removal and four decoded exports pass.'),before=before,after=after))
initials=[]
for family in ['forest','cumulative','leave-one-out','subgroup','regression','sroc','coefficient','funnel','contour','trimfill','deeks']:
 attempts=[json.loads(p.read_text()) for p in (h/'raw').glob('review1-native-editor-'+family+'*.json')]
 passed=sorted((r for r in attempts if r['exit_code']==0),key=lambda r:r['finished'])
 if not passed:continue
 attempt=passed[-1]
 p=Path(re.search(r'Evidence: (.+)',(h/'raw'/attempt['log']).read_text())[1])
 action=next(r for r in map(json.loads,(p/'steps.jsonl').read_text().splitlines()) if r['action']=='review1-caption-initial')
 source=p/action['captures'][0]
 same=next((r for r in rows if r['sha256']==hashlib.sha256(source.read_bytes()).hexdigest()),None)
 target=str(Path(same['destination']).relative_to(h.relative_to(root))) if same else copy(source,'editor-'+family+'-initial')
 initials.append(dict(family=family,label=attempt['label'],image=target,source=str(source.relative_to(root))))
assert len(initials)==11, len(initials)
(h/'REVIEW1-EDITOR-INITIALS.json').write_text(json.dumps(initials,indent=2)+'\n')
(h/'REVIEW1-CURATION.json').write_text(json.dumps(rows,indent=2)+'\n');(h/'REVIEW1-EDITOR-PAIRS.json').write_text(json.dumps(pairs,indent=2)+'\n');print(len(pairs),'editor pairs')
