from pathlib import Path
import sys
from xml.etree import ElementTree as ET
sys.path.insert(0, str(Path.cwd()))
from tests.e2e.axis_conventions import ticks
folder=Path(sys.argv[1])
failures=[]
for path in sorted(folder.glob('*.svg')):
 observed=ticks(path)
 if len(observed)!=6 or observed[-1][0]!=1:
  rows=[(n.text,n.attrib.get('y'),n.attrib.get('x')) for n in ET.parse(path).iter('{http://www.w3.org/2000/svg}text')]
  failures.append((str(path),observed,rows))
print(f'{len(failures)} of {len(list(folder.glob("*.svg")))} real SVG text rows mis-grouped.')
for row in failures[:4]:print(row)
assert not failures
