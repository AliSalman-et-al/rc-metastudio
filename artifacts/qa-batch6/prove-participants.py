import json, zipfile, difflib
from pathlib import Path
root=Path(__file__).resolve().parents[2]
project=json.loads(zipfile.ZipFile(root/'sample_projects/lymph.rcms').read('project.json'))
rows=project['sheets'][0]['rows']
counts=[(row['label'], next(iter(row['raw_data'].values()))) for row in rows if row['include']]
assert all(len(c)==4 for _,c in counts)
total=sum(sum(c) for _,c in counts)
assert total==1408
print('Independent ZIP/JSON sum, TP+FN+FP+TN:')
for name,c in counts: print(name, c, sum(c))
print('Included studies:',len(counts),'Participants:',total)
evidence=Path(__file__).resolve().parent
a=(evidence/'before-report.txt').read_text()
b=(evidence/'after-report.txt').read_text()
print(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True))))
assert '1408' in b
assert a.replace('Not available','1408')==b
assert (evidence/'before-model-texts.json').read_bytes()==(evidence/'after-model-texts.json').read_bytes()
print('PASS: entire clinical report identical except Participants; all model result text identical.')
