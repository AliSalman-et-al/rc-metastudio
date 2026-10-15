"""Confirm bundled BCG arm direction against the pinned metadat source."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

from rc_metastudio.project_format import load_project

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
command = [str(Path(os.environ['RCMS_R_HOME']) / 'bin/Rscript'), '--vanilla', '-e',
    'cat(jsonlite::toJSON(list(package=as.character(packageVersion("metadat")), rows=metadat::dat.bcg), dataframe="rows", auto_unbox=TRUE))']
source = json.loads(subprocess.check_output(command, text=True))
project = load_project(ROOT / 'sample_projects/BCG.rcms')
studies = project.project['dataset']['studies']
assert len(studies) == len(source['rows']) == 13
for study, row in zip(studies, source['rows'], strict=True):
    assert study['year'] == row['year']
    unit = next(unit for unit in study['analysis_units'] if unit['follow_up'] == 'first')
    groups = sorted(unit['groups'], key=lambda group: group['id'])
    assert groups[0]['name'] == 'BCG vaccine' and groups[1]['name'] == 'Control'
    assert groups[0]['raw_data'] == [row['tpos'], row['tpos'] + row['tneg']]
    assert groups[1]['raw_data'] == [row['cpos'], row['cpos'] + row['cneg']]
proof = dict(passed=True, command=command, source='metadat::dat.bcg', **source,
    source_meaning='The pinned dataset help identifies tpos/tneg as vaccinated TB-positive/negative counts, and cpos/cneg as non-vaccinated control counts.',
    publication='Colditz et al. (1994), JAMA 271(9), 698–702', doi='10.1001/jama.1994.03510330076038',
    project_sha256=hashlib.sha256((ROOT / 'sample_projects/BCG.rcms').read_bytes()).hexdigest(),
    conclusion='All 13 stored rows match the source with arm 0 vaccinated and arm 1 control; labels preserve the original direction.')
(HERE / 'REVIEW1-BCG-SOURCE.json').write_text(json.dumps(proof, indent=2) + '\n')
print('All 13 BCG rows match pinned metadat 1.6-0: vaccinated / non-vaccinated control; original direction preserved.')
