"""Real Qt/R evidence for the whole-app review's palette and report fixes."""
from PyQt6 import QtCore, QtGui, QtWidgets
import re
import gzip
from pathlib import Path
from xml.etree import ElementTree as ET
from tests.python.gui.qt_test_support import wait, mouse_click


def contrast(foreground, background):
    def luminance(color):
        values = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
                  for v in (color.redF(), color.greenF(), color.blueF())]
        return sum(a * b for a, b in zip(values, (.2126, .7152, .0722)))
    light, dark = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (light + .05) / (dark + .05)


def rendered_text(widget, rect):
    image = widget.grab().toImage()
    scale = image.devicePixelRatio()
    background = widget.palette().color(QtGui.QPalette.ColorRole.Window)
    pixels = [image.pixelColor(round(x * scale), round(y * scale))
              for y in range(rect.top() + 3, rect.bottom() - 2)
              for x in range(rect.left() + 24, rect.right() - 4)]
    count = sum(contrast(pixel, background) >= 4.5 for pixel in pixels)
    assert count >= 15, (widget.objectName(), count, background.name())
    return count


def funnel_clip_evidence(view, artifact, work):
    from rc_metastudio.results_window import _opaque_svg_renderer
    from rc_metastudio.manuscript_report import figure_source

    svg = Path(artifact.display_path())
    assert svg.suffix == '.svg', 'Funnels must use vector Results artifacts'
    payload = svg.read_bytes()
    root = ET.fromstring(gzip.decompress(payload) if payload.startswith(b'\x1f\x8b') else payload)
    assert not list(root.iter('{http://www.w3.org/2000/svg}image')), 'Embedded raster in funnel SVG'
    rectangles = [node for clip in root.iter('{http://www.w3.org/2000/svg}clipPath')
                  for node in clip if node.tag.endswith('rect')]
    clip = min(rectangles, key=lambda node: float(node.attrib['width']) * float(node.attrib['height']))
    vx, vy, vw, vh = map(float, root.attrib['viewBox'].split())
    colors = set()
    for node in root.iter():
        match = re.search(r'fill:\s*(#[0-9A-Fa-f]{6})', node.attrib.get('style', ''))
        if match:
            color = QtGui.QColor(match[1])
            channels = color.red(), color.green(), color.blue()
            if min(channels) >= 100 and max(channels) - min(channels) > 2:
                colors.add(color.rgb())
    measurements = []
    for surface, renderer in [('results', _opaque_svg_renderer(str(svg), None)),
                              ('manuscript', figure_source(svg)[0])]:
        assert renderer.isValid()
        for scale in (1, 2):
            image = QtGui.QImage(round(vw * scale), round(vh * scale), QtGui.QImage.Format.Format_RGB32)
            image.fill(QtCore.Qt.GlobalColor.white)
            painter = QtGui.QPainter(image)
            renderer.render(painter)
            painter.end()
            left = (float(clip.attrib['x']) - vx) * image.width() / vw
            top = (float(clip.attrib['y']) - vy) * image.height() / vh
            right = left + float(clip.attrib['width']) * image.width() / vw
            bottom = top + float(clip.attrib['height']) * image.height() / vh
            outside = inside = 0
            for y in range(image.height()):
                for x in range(image.width()):
                    if image.pixel(x, y) in colors:
                        if x < left - 2 or x > right + 2 or y < top - 2 or y > bottom + 2:
                            outside += 1
                        else:
                            inside += 1
            assert outside == 0, (artifact.title, surface, scale, outside)
            if colors:
                assert inside > 1000 * scale * scale, (artifact.title, surface, inside)
            retained = work / (svg.stem + f'-{surface}-{scale}x.png')
            assert image.save(str(retained))
            measurements.append(dict(surface=surface, scale=scale, outside_region_pixels=outside,
                                     inside_region_pixels=inside, rendered_path=str(retained)))
    return dict(vector_path=str(svg), measurements=measurements)


def run(app, window, work, root, record, analyze):
    from rc_metastudio.analysis_setup_dialog import AnalysisSetupDialog
    from rc_metastudio.about_legal_dialog import AboutLegalDialog
    from rc_metastudio.main_wizard import MainWizard, Page_CsvImport, CsvImportPage
    from tests.e2e.report_retention import assert_report

    assert window.open(str(root / 'sample_projects/amino.rcms'), raise_on_error=True)
    window.showNormal()
    window.resize(1280, 800)
    setup = AnalysisSetupDialog(window.model, parent=window, confidence_level=95)
    setup.show()
    wizard = MainWizard(path='csv_import')
    wizard.set_dataset_info(dict(arms='two', data_type='binary', sub_type='proportions', effect='OR', metric_choices=[], name='Mortality'))
    wizard.setStartId(Page_CsvImport)
    wizard.restart()
    wizard.show()
    csv = wizard.currentPage()
    assert isinstance(csv, CsvImportPage)
    error = csv.import_status
    csv.file_path = str(work / 'missing-review.csv')
    csv._rebuild_display()
    assert error.text() and not csv.imported_data_ok
    about = AboutLegalDialog(window)
    about.show()
    assert getattr(app, '_rcms_error_palette', None) is not None
    assert error.property('rcmsInlineError')
    original_palette = app.palette()
    for name, scheme in [('dark', QtCore.Qt.ColorScheme.Dark), ('light', QtCore.Qt.ColorScheme.Light), ('dark-again', QtCore.Qt.ColorScheme.Dark)]:
        app.styleHints().setColorScheme(scheme)
        wait(150)
        for menu in (window.menuAnalysis, window.analysis_button.menu()):
            menu.popup(window.mapToGlobal(QtCore.QPoint(200, 80)))
            wait(80)
            action = next(a for a in menu.actions() if a.isEnabled() and not a.isSeparator())
            record('polish-menu-' + name, menu, text_pixels=rendered_text(menu, menu.actionGeometry(action)))
            menu.close()
        setup.raise_()
        for expanded in (False, True):
            setup.advanced_toggle.setChecked(expanded)
            wait(50)
            count = rendered_text(setup.advanced_toggle, setup.advanced_toggle.rect())
            record('polish-advanced-' + name, setup, expanded=expanded, text_pixels=count)
        wizard.raise_()
        csv.csv_options_btn.setChecked(True)
        wait(50)
        assert rendered_text(csv.csv_options_btn, csv.csv_options_btn.rect()) >= 15
        ratio = contrast(error.palette().color(error.foregroundRole()), error.palette().color(error.backgroundRole()))
        assert ratio >= 4.5, ratio
        expected = '#ff9ca8' if error.palette().color(error.backgroundRole()).lightness() < 128 else '#b00020'
        assert error.palette().color(error.foregroundRole()).name() == expected
        record('polish-import-' + name, wizard, error_contrast=ratio)
        about.raise_()
        record('polish-about-' + name, about)
    for name, background, foreground in [('custom-dark', '#25272b', '#f0f0f0'), ('custom-light', '#f5f5f5', '#202020')]:
        palette = QtGui.QPalette(original_palette)
        for role in (QtGui.QPalette.ColorRole.Window, QtGui.QPalette.ColorRole.Button, QtGui.QPalette.ColorRole.Base):
            palette.setColor(role, QtGui.QColor(background))
        for role in (QtGui.QPalette.ColorRole.WindowText, QtGui.QPalette.ColorRole.ButtonText, QtGui.QPalette.ColorRole.Text):
            palette.setColor(role, QtGui.QColor(foreground))
        app.setPalette(palette)
        wizard.raise_()
        wait(100)
        error_image = error.grab().toImage()
        red_pixels = sum((color := error_image.pixelColor(x, y)).red() > color.green() * 1.2
                         and color.red() > color.blue()
                         for y in range(error_image.height()) for x in range(error_image.width()))
        assert red_pixels >= 10, (name, red_pixels)
        assert contrast(error.palette().color(error.foregroundRole()), error.palette().color(error.backgroundRole())) >= 4.5, (name, error.palette().color(error.foregroundRole()).name(), error.palette().color(error.backgroundRole()).name())
        assert error.palette().color(error.foregroundRole()).name() == ('#ff9ca8' if error.palette().color(error.backgroundRole()).lightness() < 128 else '#b00020')
        assert rendered_text(setup.advanced_toggle, setup.advanced_toggle.rect()) >= 15
        wizard.raise_()
        record('polish-import-' + name, wizard)
    app.setPalette(original_palette)
    valid = work / 'recovered-review.csv'
    valid.write_text('Study Name,Year,Intervention events,Intervention total,Control events,Control total\nStudy,2020,5,20,8,20\n')
    csv.file_path = str(valid)
    csv.has_headers_chkbx.setChecked(True)
    csv._rebuild_display()
    wait(50)
    assert csv.imported_data_ok and error.text().startswith('Ready to import')
    assert error.palette().color(error.foregroundRole()) == csv.palette().color(error.foregroundRole())
    record('polish-import-recovered', wizard)
    about.close()
    wizard.reject()
    setup.reject()
    view = analyze(app, window, 'binary.random')
    view.showNormal()
    available = view.screen().availableGeometry()
    view.resize(min(1200, available.width() - 48), min(680, available.height() - 64))
    view.move(available.left() + 24, available.top() + 24)
    assert_report(view)
    for name, scheme in [('light', QtCore.Qt.ColorScheme.Light), ('dark', QtCore.Qt.ColorScheme.Dark), ('light-again', QtCore.Qt.ColorScheme.Light)]:
        app.styleHints().setColorScheme(scheme)
        wait(150)
        assert all(contrast(item.defaultTextColor(), view.palette().color(view.backgroundRole())) >= 4.5
                   for item in view._wrapped_text_items)
        view.content_stack.setCurrentWidget(view.figure_page)
        record('polish-figure-' + name, view)
        view.nav_tree.setCurrentItem(view.nav_tree.findItems('Manuscript', QtCore.Qt.MatchFlag.MatchExactly)[0])
        record('polish-manuscript-' + name, view)
        model_fit = next(s for s in view.manuscript.sections if s.title == 'Model fit')
        assert model_fit.paragraphs
        view.manuscript_text.moveCursor(QtGui.QTextCursor.MoveOperation.Start)
        assert view.manuscript_text.find(model_fit.paragraphs[0])
        cursor = view.manuscript_text.textCursor()
        cursor.clearSelection()
        view.manuscript_text.setTextCursor(cursor)
        scrollbar = view.manuscript_text.verticalScrollBar()
        assert scrollbar is not None
        scrollbar.setValue(min(scrollbar.maximum(), scrollbar.value() + view.manuscript_text.viewport().height() // 2))
        record('polish-interval-note-' + name, view)
        view.manuscript_text.moveCursor(QtGui.QTextCursor.MoveOperation.Start)
        supplementary = next(s for s in view.manuscript.sections if s.title == 'Supplementary details' and s.tables)
        assert view.manuscript_text.find(supplementary.tables[0].title)
        scrollbar.setValue(min(scrollbar.maximum(), scrollbar.value() + view.manuscript_text.viewport().height() // 2))
        record('polish-supplementary-' + name, view)
        view.tables_action.trigger()
        view.table_selector.setCurrentIndex(0)
        table = view.result_table
        assert table.horizontalHeader().font().bold()
        assert sum(table.columnWidth(i) for i in range(table.columnCount())) < table.viewport().width(), 'compact summary fills viewport'
        record('polish-tables-' + name, view)
    view.close()
    from analysis_matrix import run as matrix
    for scenario in ('small-study-binary-extended', 'analysis-amino-binary-subgroup', 'analysis-diagnostic-joint', 'small-study-diagnostic'):
        window.workspace.mark_saved()
        view = matrix(app, window, scenario, record, keep_results=True)
        view.showNormal()
        view.resize(1280, 800)
        wait(100)
        assert_report(view)
        if scenario == 'small-study-binary-extended':
            view.nav_tree.setCurrentItem(view.nav_tree.findItems('Manuscript', QtCore.Qt.MatchFlag.MatchExactly)[0])
            unstructured = next(t for s in view.manuscript.sections if s.title == 'Supplementary details' for t in s.tables if t.headers == ('',))
            assert view.manuscript_text.find(unstructured.title)
            bar = view.manuscript_text.verticalScrollBar()
            assert bar is not None
            bar.setValue(min(bar.maximum(), bar.value() + view.manuscript_text.viewport().height() // 2))
            record('polish-unstructured-supplementary', view)
        view._explicit_fit_width = False
        for nav_id, item in view._nav_items_to_sections.items():
            if item not in (*view._svg_plot_items, *view._raster_plot_items):
                continue
            nav = next(view.nav_tree.topLevelItem(i) for i in range(view.nav_tree.topLevelItemCount())
                       if id(view.nav_tree.topLevelItem(i)) == nav_id)
            view.nav_tree.setCurrentItem(nav)
            view._show_report(False)
            view._explicit_fit_width = False
            view._apply_fit_width()
            rect = item.sceneBoundingRect()
            viewport = view.graphics_view.viewport()
            assert viewport is not None
            text_pt = None
            if item in view._svg_plot_items:
                renderer = item.renderer()
                text_size = renderer.property('body_text_size')
                text_pt = text_size * item.boundingRect().width() / renderer.viewBoxF().width() * item.scale() * 72 / 96 if text_size else None
                assert text_pt is None or text_pt >= 9
                if text_pt and text_pt > 9.01 and not str(item.data(0)).endswith('forest'):
                    assert rect.height() <= viewport.height() - 20, (nav.text(0), rect, viewport.size())
            else:
                raise AssertionError('Expected a vector plot for ' + nav.text(0))
            artifact = view._nav_plot_artifacts[nav_id]
            if artifact.capability.regenerator == 'funnel':
                assert item in view._svg_plot_items
                record('polish-funnel-region-clip', view, title=nav.text(0), **funnel_clip_evidence(view, artifact, work))
            record('polish-initial-square-' + scenario, view, title=nav.text(0),
                   plot_bounds=[rect.width(), rect.height()], viewport=[viewport.width(), viewport.height()], body_text_pt=text_pt)
            view.fit_width_action.trigger()
            assert item.sceneBoundingRect().width() >= viewport.width() * .9
            record('polish-explicit-fit-width', view, title=nav.text(0))
        view.close()
