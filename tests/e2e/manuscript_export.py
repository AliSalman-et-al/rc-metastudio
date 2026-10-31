"""Reopen real manuscript exports and compare with the executed result."""
from unittest.mock import patch
import subprocess
import unicodedata
from docx import Document
from PyQt6 import QtWidgets


def run(app, window, work, root, record, analyze):
    for sample, method in (("amino", "binary.random"), ("continuous", "continuous.random"), ("lymph", "diagnostic.reitsma"), ("Pignon2000-HR", "time_to_event.random")):
        window.workspace.mark_saved()
        assert window.open(str(root / 'sample_projects' / (sample + '.rcms')), raise_on_error=True)
        view = analyze(app, window, method)
        for suffix in ('pdf', 'docx'):
            path = work / (sample + '.' + suffix)
            def picker(*args, **kwargs):
                dialog = QtWidgets.QFileDialog(view)
                dialog.setOption(QtWidgets.QFileDialog.Option.DontUseNativeDialog)
                dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptSave)
                dialog.setNameFilter('Report (*.' + suffix + ')')
                dialog.selectFile(str(path))
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(0, dialog.accept)
                assert dialog.exec()
                return dialog.selectedFiles()[0], dialog.selectedNameFilter()
            with patch.object(QtWidgets.QFileDialog, 'getSaveFileName', side_effect=picker):
                view.export_report_action.trigger()
            assert path.exists()
            if suffix == 'docx':
                doc = Document(path)
                assert doc.paragraphs[0].text == view.manuscript.title
                assert 'Table 1.' in '\n'.join(p.text for p in doc.paragraphs)
                if sample == 'amino':
                    assert doc.tables[0].rows[0].cells[0].text == 'Statistic'
                assert len(doc.inline_shapes) >= len(view.results.images)
                assert all(round(s.width / 36000) in (85, 180) for s in doc.inline_shapes)
                text = '\n'.join(p.text for p in doc.paragraphs) + '\n' + '\n'.join(c.text for t in doc.tables for r in t.rows for c in r.cells)
            else:
                text = subprocess.check_output(['pdftotext', '-layout', str(path), '-']).decode()
            assert 'Methods' in text and 'RC MetaStudio' in ' '.join(text.split())
            normalized = ' '.join(unicodedata.normalize('NFKC', text).split())
            for prose in (view.manuscript.methods, view.manuscript.results):
                assert ' '.join(unicodedata.normalize('NFKC', prose).split()) in normalized, (sample, suffix, prose, normalized)
            assert view.manuscript_methods.toPlainText() == view.manuscript.methods
            assert view.manuscript_results.toPlainText() == view.manuscript.results
            assert all(value not in text for value in ('executed settings', 'Project:', '.rcms'))
            assert 'Supplementary details' in text
            if sample == 'amino':
                assert view.manuscript.title == 'clinical failure: random-effects meta-analysis (odds ratio)'
                assert 'The pooled odds ratio was 0.770 (95% CI 0.485 to 1.222; p = 0.267).' in view.manuscript.results
                assert view.manuscript.results == '19 studies were included (1097 participants in Intervention, 1080 in Control). The pooled odds ratio was 0.770 (95% CI 0.485 to 1.222; p = 0.267). Heterogeneity: Q = 33.360 (df = 18; p = 0.015), I² = 46.0%, τ² = 0.378. The 95% prediction interval was 0.212 to 2.799.'
                assert view.manuscript.methods == "Odds ratios were pooled using a random-effects model with the DerSimonian–Laird estimator of between-study variance. Confidence intervals (95%) used the normal approximation. A continuity correction of 0.5 was applied to studies with any zero cell. Heterogeneity was assessed with Cochran's Q and I². Analyses were performed in RC MetaStudio 0.5.0. R packages loaded for this analysis: metafor 5.0.1, meta 8.5-0."
                assert '-0.262' in normalized
            record('manuscript-export-' + sample + '-' + suffix, view, exported=str(path))
        (work / (sample + '-prose.txt')).write_text('Methods\n' + view.manuscript.methods + '\n\nResults\n' + view.manuscript.results)
        item = view.nav_tree.findItems('Manuscript', __import__('PyQt6.QtCore', fromlist=['Qt']).Qt.MatchFlag.MatchExactly)[0]
        view.nav_tree.setCurrentItem(item)
        record('manuscript-panel-' + sample, view)
        view.close()

    import sys
    sys.path.insert(0, str(root / ".agents/skills/verify-rcms/scripts"))
    from tests.e2e.audit_round3 import analyze_existing
    for workflow in ('subgroup', 'meta-regression'):
        window.workspace.mark_saved()
        assert window.open(str(root / 'sample_projects/amino.rcms'), raise_on_error=True)
        studies = window.model.get_studies()
        window.model.add_covariate('Group', 'factor', {s.label: 'A' if i % 2 else 'B' for i, s in enumerate(studies)})
        window.model.add_covariate('Dose', 'continuous', {s.label: float(i + 1) for i, s in enumerate(studies)})
        window.model.reset_model()
        window.enable_menu_options_that_require_dataset()
        view = analyze_existing(app, window, workflow, 'binary.random', record)
        from rc_metastudio.manuscript_report import write_docx, write_pdf
        write_docx(view.manuscript, work / (workflow + '.docx'))
        write_pdf(view.manuscript, work / (workflow + '.pdf'))
        assert workflow.split('-')[0].lower() in view.manuscript.methods.lower()
        (work / (workflow + '-prose.txt')).write_text('Methods\n' + view.manuscript.methods + '\n\nResults\n' + view.manuscript.results)
        record('manuscript-' + workflow, view)
        view.close()
