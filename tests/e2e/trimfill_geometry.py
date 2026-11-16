"""Match vector preview geometry and exported markers to an independent fit."""
import re
import gzip
import sys
from pathlib import Path
from typing import cast
from rpy2.robjects.functions import SignatureTranslatedFunction
from xml.etree import ElementTree as ET
from rpy2 import robjects as ro


def check_trimfill(view, record):
    checked = 0
    for title, image in view.results.images.items():
        if 'trim-and-fill' not in title.lower():
            continue
        checked += 1
        directory = Path(sys.argv[2]) / 'trimfill-geometry'
        directory.mkdir(exist_ok=True)
        path = directory / ('right.svg' if 'right' in title.lower() else 'left.svg')
        view.plot_service.export(regenerator='funnel', params_path=view.results.image_params_paths[title], output_path=str(path))
        params = view.plot_service.load_params(view.results.image_params_paths[title])
        filled = list(params['trimfill.imputed'])
        y = list(params['prepared.effects'])
        se = list(params['prepared.standard.errors'])
        observed = [i for i, fill in enumerate(filled) if not fill]
        trimfill = cast(SignatureTranslatedFunction, ro.r(
            'function(y,se,side) metafor::trimfill(metafor::rma(yi=y,sei=se,method="REML"),side=side)'))
        fit = trimfill(
            ro.FloatVector([y[i] for i in observed]), ro.FloatVector([se[i] for i in observed]),
            'right' if 'right' in title.lower() else 'left')
        k0 = int(fit.rx2('k0')[0])
        payload = path.read_bytes()
        root = ET.fromstring(gzip.decompress(payload) if payload.startswith(b'\x1f\x8b') else payload)
        assert Path(image).suffix == '.svg'
        assert ET.canonicalize(from_file=image) == ET.canonicalize(from_file=path), 'Preview differs from its exported geometry'
        circles = list(root.iter('{http://www.w3.org/2000/svg}circle'))
        hollow = [node for node in circles if node.attrib.get('fill') == 'none' or 'fill: none' in node.attrib.get('style', '')]
        assert len(observed) == 17, len(observed)
        assert sum(filled) == k0, (title, sum(filled), k0)
        assert len(circles) == len(observed) + k0, (title, len(circles), len(observed), k0)
        assert len(hollow) == k0, (title, len(hollow), k0)
        assert ('No studies imputed' in ''.join(root.itertext())) == (k0 == 0)
        record('trimfill-marker-count', view, title=title, observed=len(observed), k0=k0,
               markers=len(circles), hollow=len(hollow), geometry_svg=str(path), preview_geometry_matches=True)

    assert checked == 2, checked
