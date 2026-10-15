"""Deduplicate actual recorded runtime UI strings with first-occurrence pointers."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
seen={};reports=0;steps=0
for receipt in sorted((HERE/'raw').glob('helper-*.json')):
 data=json.loads(receipt.read_text());log=HERE/'raw'/data['log']
 evidence=next((Path(l[10:]) for l in log.read_text().splitlines() if l.startswith('Evidence: ')),None)
 if not evidence or not (evidence/'steps.jsonl').exists():continue
 for line in (evidence/'steps.jsonl').read_text().splitlines():
  row=json.loads(line);steps+=1
  for item in row.get('visible_labels',[]):
   text=item['text']
   if len(text)>600:reports+=1;continue
   kind='tooltip' if item['surface'].endswith(':tooltip') else 'choice' if item['surface'].endswith(':choice') else 'label'
   key=(kind,text)
   if key not in seen:seen[key]={'kind':kind,'text':text,'surface':item['surface'],'scenario':receipt.stem.removeprefix('helper-'),'step':row['step'],'action':row['action'],'steps_file':str(evidence/'steps.jsonl')}
out={'scope':'Actual visible Qt widgets; tooltip properties and all choices of visible combos. This inventories text, not proof that every tooltip/popup was physically shown. Long report bodies remain in steps/raw report exports. Includes interrupted/failure evidence with scenario pointers, never reclassifies it as pass.','steps_read':steps,'long_report_occurrences_kept_in_source':reports,'strings':sorted(seen.values(),key=lambda r:(r['kind'],r['text']))}
(HERE/'TEXT-INVENTORY.json').write_text(json.dumps(out,indent=2)+'\n')
print('steps',steps,'unique UI strings',len(seen))
