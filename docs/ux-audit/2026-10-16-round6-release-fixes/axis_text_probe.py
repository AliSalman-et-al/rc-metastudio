from pathlib import Path
import sys
from xml.etree import ElementTree as ET
sys.path.insert(0, str(Path.cwd()))
from tests.e2e.axis_conventions import ticks
folder=Path(sys.argv[1])
expected = {f'{family}-{height / 100:g}.svg' for family in ('sans', 'serif', 'Arial', 'Liberation-Sans') for height in range(200, 211)}
observed_files = {path.name for path in folder.glob('*.svg')}
assert observed_files == expected, ('SVG inventory differs', sorted(expected - observed_files), sorted(observed_files - expected))
failures=[]
for path in sorted(folder.glob('*.svg')):
 observed=ticks(path)
 if [value for value, *_ in observed] != [0, .2, .4, .6, .8, 1]:
  rows=[(n.text,n.attrib.get('y'),n.attrib.get('x')) for n in ET.parse(path).iter('{http://www.w3.org/2000/svg}text')]
  failures.append((str(path),observed,rows))
print(f'{len(failures)} of {len(list(folder.glob("*.svg")))} real SVG text rows mis-grouped.')
for row in failures[:4]:print(row)
assert not failures
