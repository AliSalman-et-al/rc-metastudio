"""Retain the unchanged diagnostic title/tick clearance measurement for display/export."""
import hashlib
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
selected = json.loads((HERE / 'NATIVE-SELECTED.json').read_text())
receipt = next(row for row in selected if row['scenario'] == 'audit-round3-presentation-diagnostic')
directory = ROOT / receipt['evidence']
steps = [json.loads(line) for line in (directory / 'steps.jsonl').read_text().splitlines()]
rows = []


def box(node):
    x, y = float(node.attrib['x']), float(node.attrib['y'])
    width = float(node.attrib['textLength'].removesuffix('px'))
    height = float(re.search(r'font-size: ([\d.]+)px', node.attrib['style'])[1])
    anchor = node.attrib.get('text-anchor', 'start')
    left = x-width if anchor == 'end' else x-width/2 if anchor == 'middle' else x
    return left, left+width, y-height, y


for step in steps:
    if step['action'] != 'round4-annotations':
        continue
    title, style, digits = step['title'], step['style'], step['digits']
    paths = {'display': directory / step['artifacts'][title],
             'export': directory / 'workflow' / f'diagnostic-{style}-{digits}-{title}.svg'}
    for kind, path in paths.items():
        nodes = list(ET.parse(path).iter('{http://www.w3.org/2000/svg}text'))
        gaps = []
        for label in (node for node in nodes if ''.join(node.itertext()) in {'Sensitivity', 'Specificity'}):
            a = box(label)
            for tick in (node for node in nodes if re.fullmatch(r'0\.[\d]+', ''.join(node.itertext()))):
                b = box(tick)
                if abs(b[3]-a[3]) < 30 and min(a[1], b[1]) > max(a[0], b[0]):
                    gap = max(a[2]-b[3], b[2]-a[3])
                    assert gap >= 4, (path, a, b, gap)
                    gaps.append(gap)
        assert gaps, path
        rows.append(dict(style=style, digits=digits, title=title, kind=kind,
                         source=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         minimum_gap_points=min(gaps), required_gap_points=4))
assert len(rows) == 24, len(rows)
result = dict(passed=True, native_manifest_sha256=receipt['manifest_sha256'], cases=12,
              svg_artifacts=24, minimum_gap_points=min(row['minimum_gap_points'] for row in rows), rows=rows)
(HERE / 'AXIS-TITLE-GEOMETRY.json').write_text(json.dumps(result, indent=2) + '\n')
print(f'12 native diagnostic configurations, 24 display/export SVGs: minimum title/tick gap {result["minimum_gap_points"]:.2f} points (required 4).')
