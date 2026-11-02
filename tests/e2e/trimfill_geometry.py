"""Count actual display markers against the fit and an independent metafor fit."""
import re
from xml.etree import ElementTree as ET
from rpy2 import robjects as ro


def check_trimfill(view, record):
    checked = 0
    for title, image in view.results.images.items():
        if 'trim-and-fill' not in title.lower():
            continue
        checked += 1
        path = view.results.display_images.get(title, image)
        params = view.plot_service.load_params(view.results.image_params_paths[title])
        filled = list(params['trimfill.imputed'])
        y = list(params['prepared.effects'])
        se = list(params['prepared.standard.errors'])
        observed = [i for i, fill in enumerate(filled) if not fill]
        fit = ro.r('function(y,se,side) metafor::trimfill(metafor::rma(yi=y,sei=se,method="REML"),side=side)')(
            ro.FloatVector([y[i] for i in observed]), ro.FloatVector([se[i] for i in observed]),
            'right' if 'right' in title.lower() else 'left')
        k0 = int(fit.rx2('k0')[0])
        root = ET.parse(path).getroot()
        circles = list(root.iter('{http://www.w3.org/2000/svg}circle'))
        hollow = [node for node in circles if node.attrib.get('fill') == 'none' or 'fill: none' in node.attrib.get('style', '')]
        assert len(observed) == 17, len(observed)
        assert sum(filled) == k0, (title, sum(filled), k0)
        assert len(circles) == len(observed) + k0, (title, len(circles), len(observed), k0)
        assert len(hollow) == k0, (title, len(hollow), k0)
        assert ('No studies imputed' in ''.join(root.itertext())) == (k0 == 0)
        record('trimfill-marker-count', view, title=title, observed=len(observed), k0=k0,
               markers=len(circles), hollow=len(hollow), display_svg=str(path))

    assert checked == 2, checked
