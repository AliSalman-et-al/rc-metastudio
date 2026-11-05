"""Compare the installed R and Python display rules against the reviewed examples."""
import json
import os
from pathlib import Path
import subprocess
from rc_metastudio.result_sections import format_effect_number

cases = [(3, [0.77, 0.783, 1.2, 1.285, 0.24, 0.58],
          ['0.770', '0.783', '1.200', '1.285', '0.240', '0.580']),
         (2, [0.004, 0.0088, 0.00004], ['0.004', '0.0088', '0.00004'])]
observed = []
for digits, values, expected in cases:
    python = [format_effect_number(v, digits) for v in values]
    vector = ','.join(map(str, values))
    script = f'library(RCMetaR);cat(jsonlite::toJSON(RCMetaR:::rcmetar.format.effect.number(c({vector}),{digits})))'
    r = json.loads(subprocess.check_output([os.environ['RCMS_R_HOME']+'/bin/Rscript', '-e', script], text=True))
    assert python == r == expected, (python, r, expected)
    observed.append(dict(digits=digits, values=values, expected=expected, python=python, r=r))
Path(__file__).with_name('formatting-proof.json').write_text(json.dumps(observed, indent=2)+'\n')
print('Python and installed R preserve fixed decimals and agree on all adaptive examples.')
