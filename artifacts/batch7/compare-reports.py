import json, pathlib, difflib
root=pathlib.Path(__file__).parent
out=[]
for sample in ('continuous','amino'):
 before=json.loads((root/f'before-{sample}-descriptor.json').read_text())
 after=json.loads((root/f'after-{sample}-descriptor.json').read_text())
 for phase,data in [('before',before),('after',after)]:
  (root/f'{phase}-{sample}-report.txt').write_text('\n\n'.join(f'{k}\n{v}' for k,v in data['texts'].items()))
  (root/f'{phase}-{sample}-plot-text.txt').write_text('\n'.join(x['text'] for x in data['visible_plot_labels']))
 for kind in ('report','plot-text'):
  a=(root/f'before-{sample}-{kind}.txt').read_text().splitlines();b=(root/f'after-{sample}-{kind}.txt').read_text().splitlines()
  out.extend(difflib.unified_diff(a,b,fromfile=f'before-{sample}-{kind}',tofile=f'after-{sample}-{kind}',lineterm=''))
(root/'presentation.diff').write_text('\n'.join(out)+'\n')
