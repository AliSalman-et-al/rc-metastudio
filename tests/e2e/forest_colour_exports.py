"""Forest colour settings and decoded colour export workflows."""

from rc_metastudio.qt_object_guard import required
import os
from pathlib import Path
from xml.etree import ElementTree as ET
from PyQt6 import QtCore, QtWidgets
from tests.e2e.plot_workflow_support import close


def check_colours(path, colour='#2F5597', require_caps=True):
    """Check rendered study boxes, CIs, caps, arrows and summary diamonds."""
    import re
    root = ET.parse(path)
    polygons = list(root.iter('{http://www.w3.org/2000/svg}polygon'))
    assert polygons, path
    y = [float(point.split(',')[1]) for node in polygons for point in node.attrib['points'].split()]
    top, bottom = min(y), max(y)
    def paint(node, name):
        found = re.search(r'(?:^|;)\s*' + name + r':\s*([^;]+)', node.attrib.get('style',''))
        return (found[1] if found else node.attrib.get(name, '#000000')).upper()
    for node in root.iter('{http://www.w3.org/2000/svg}text'):
        if ''.join(node.itertext()).startswith('Fixture '):
            assert paint(node,'fill') == '#000000', ('study label colour', node.attrib)
    for node in polygons:
        assert paint(node, 'fill') == colour, (path, 'marker/diamond/arrow', node.attrib)
    paper_width = float(root.getroot().attrib['viewBox'].split()[2])
    intervals = []
    caps = []
    for node in root.iter('{http://www.w3.org/2000/svg}line'):
        x1,y1,x2,y2 = (float(node.attrib[k]) for k in ('x1','y1','x2','y2'))
        if top <= y1 <= bottom and top <= y2 <= bottom:
            if abs(y1-y2) < .02 and 1 < abs(x1-x2) < paper_width*.8:
                intervals.append(node)
            elif abs(x1-x2) < .02 and .2 < abs(y1-y2) < 15:
                caps.append(node)
    assert intervals and (caps or not require_caps), (path, len(intervals),len(caps))
    for node in intervals + caps:
        assert paint(node,'stroke') == colour, (path, 'CI/cap', node.attrib)
    def luminance(hex_value):
        rgb = [int(hex_value[i:i+2],16)/255 for i in (1,3,5)]
        rgb = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        return sum(a*b for a,b in zip(rgb,(.2126,.7152,.0722),strict=True))
    contrast = {background:(luminance(background)+.05)/(luminance(colour)+.05) for background in ('#FFFFFF','#EEEEEE')}
    assert min(contrast.values()) >= 3, contrast
    return dict(polygons=len(polygons), intervals=len(intervals), caps=len(caps), contrast=contrast)


def run_colours(app, window, work, record):
    from analysis_matrix import run as matrix
    from advanced_workflows import export_formats, modal, click
    from rc_metastudio import r_bridge
    from rc_metastudio.plot_editor_dialog import EditPlotDialog
    from tests.e2e.analysis_presentation_workflows import analyze_existing
    baseline = bool(os.environ.get('RCMS_REVIEWER_BASELINE'))
    cases = [('analysis-amino-binary-' + workflow, None) for workflow in ('cumulative','leave-one-out','subgroup')]
    cases += [('analysis-data-' + family, metric) for family,metric in
              [('twoarm-proportion','OR'),('onearm-proportion','PFT'),('onearm-mean',None),('diagnostic',None)]]
    cases += [('HR',None),('IRR',None)]
    for scenario,metric in cases:
        window.workspace.mark_saved()
        if scenario in ('HR','IRR'):
            sample = 'Pignon2000-HR' if scenario == 'HR' else 'NielWeise2008-IRR'
            assert window.open(str(Path(__file__).resolve().parents[2]/'sample_projects'/f'{sample}.rcms'),raise_on_error=True)
            view = analyze_existing(app,window,'standard','time_to_event.random' if scenario == 'HR' else 'event_rates.random',record,{'fp_style':'default','digits':3})
        else:
            view = matrix(app,window,scenario,record,keep_results=True,metric_override=metric,parameters={'fp_style':'default'})
        for index,artifact in enumerate(view._nav_plot_artifacts.values()):
            if artifact.capability.regenerator != 'forest':
                continue
            nav = [item for item in view.nav_tree.findItems('',QtCore.Qt.MatchFlag.MatchContains | QtCore.Qt.MatchFlag.MatchRecursive) if view._nav_plot_artifacts.get(id(item)) is artifact]
            view.nav_tree.setCurrentItem(nav[0])
            view.report_action.setChecked(False)
            view._show_report(False)
            app.processEvents()
            record('reviewer-colour-before' if baseline else 'reviewer-colour-after',view,scenario=scenario,title=artifact.title,
                   plots={artifact.title:artifact.display_path()})
            if baseline:
                continue
            observed = check_colours(artifact.display_path())
            r_bridge.load_vars_for_plot(artifact.params_path,return_params_dict=True)
            r_bridge.execute_r_string('reviewer.numeric.before <- lapply(plot.data$res[vapply(plot.data$res,is.numeric,logical(1))],as.numeric)')
            def editor(dialog):
                assert dialog.style_cbo.currentText() == 'Default'
                assert dialog.style_cbo.findText('Default (metafor)') < 0
                record('reviewer-default-style-editor',dialog,scenario=scenario)
                click(app,dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel))
            modal(app,EditPlotDialog,editor,view.edit_plot_action.trigger)
            # One full export set per family, including sequential and clinical variants.
            if scenario == 'analysis-data-twoarm-proportion':
                def clipped(dialog):
                    dialog.plot_lb_le.setText('0.4')
                    dialog.plot_ub_le.setText('2')
                    click(app,dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
                modal(app,EditPlotDialog,clipped,view.edit_plot_action.trigger)
                arrows = [node for node in ET.parse(artifact.display_path()).iter('{http://www.w3.org/2000/svg}polygon') if len(node.attrib['points'].split()) == 3]
                assert arrows, 'narrow limits did not exercise clipped CI arrows'
                check_colours(artifact.display_path(),require_caps=False)
                record('reviewer-default-clipped-arrows',view,arrows=len(arrows),plots={artifact.title:artifact.display_path()})
            files = export_formats(app,view,work/f'colour-{scenario}-{index}',scenario,record)
            check_colours(files['svg'],require_caps=scenario != 'analysis-data-twoarm-proportion')
            from PIL import Image
            from PyQt6.QtPdf import QPdfDocument
            from PyQt6 import QtGui
            colour_samples = {}
            for extension in ('png','tiff','pdf'):
                if extension == 'pdf':
                    document = QPdfDocument(view)
                    assert document.load(files[extension]) == QPdfDocument.Error.None_
                    raster = document.render(0,QtCore.QSize(1200,1200)).convertToFormat(QtGui.QImage.Format.Format_RGB888)
                    image = Image.frombytes('RGB',(raster.width(),raster.height()),required(raster.bits(), "PDF raster pixels").asstring(raster.sizeInBytes()),'raw','RGB',raster.bytesPerLine())
                    document.close()
                else:
                    with Image.open(files[extension]) as source:
                        image = source.convert('RGB')
                colours = image.getcolors(1000000)
                assert colours is not None
                matches = 0
                for count, rgb in colours:
                    assert isinstance(rgb, tuple) and len(rgb) == 3, rgb
                    if max(abs(a-b) for a,b in zip(rgb,(47,85,151),strict=True)) <= 3:
                        matches += count
                assert matches > 0, ('export lacks Default blue',extension,files[extension])
                colour_samples[extension] = matches
                image.close()

            r_bridge.load_vars_for_plot(artifact.params_path,return_params_dict=True)
            assert bool(r_bridge.execute_r_string('identical(reviewer.numeric.before,lapply(plot.data$res[vapply(plot.data$res,is.numeric,logical(1))],as.numeric),num.eq=FALSE)')[0])
            record('reviewer-colour-exports',view,scenario=scenario,title=artifact.title,observed=observed,colour_samples=colour_samples,exports=files,
                   plots={artifact.title:artifact.display_path()})
        close(app,view)
