import json,re,datetime,pathlib
rows=[]
def dt(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
for p in sorted(pathlib.Path('/tmp/ci-measure').glob('*.log'),reverse=True):
 d=json.loads(p.with_suffix('.json').read_text());j=next(j for j in d['jobs'] if j['name']=='Required Windows Full R Stack Evidence');lines=p.read_text().splitlines()
 def t(pattern):
  l=next(l for l in lines if re.search(pattern,l));return dt(re.search(r'\d{4}-\d\d-\d\dT\S+Z',l)[0])
 marks=[t(x) for x in [r'Locked rpy2 identities verified',r'\[RCMetaR-r-stack\].* CMD build ',r'\[RCMetaR-r-stack\].* CMD INSTALL ',r'\[RCMetaR-r-stack\].*verify_reitsma_visual_qa.R',r'\[RCMetaR-r-stack\].* -m pytest tests\\r_stack',r'\[RCMetaR-r-stack\].* -m pytest tests/e2e',r'\[RCMetaR-r-stack\].*scripts/verify_golden_compatibility.py',r'RCMetaR R Stack Slice verification complete']]
 phases=[(marks[b]-marks[a]).total_seconds()/60 for a,b in [(0,1),(1,2),(3,4),(4,5),(5,6)]]
 total=(dt(j['completedAt'])-dt(j['startedAt'])).total_seconds()/60
 rest=total-sum(phases)
 gate=next(x for x in d['jobs'] if x['name']=='Qt6 Integration Verification Gate')
 verdict=(dt(gate['completedAt'])-dt(d['createdAt'])).total_seconds()/60
 rows.append('| ['+p.stem+']('+d['url']+') | '+' | '.join(f'{x:.2f}' for x in phases+[rest,total,verdict])+' |')
pathlib.Path('build/ci-sharding/baseline.md').write_text('| Run | R deps | R build/check | Reitsma | Bridge | Desktop | Rest | Job | Verdict |\n| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n'+'\n'.join(rows)+'\n')
