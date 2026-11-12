"""Wrapped forest arm names and full-header export workflows."""




def run_headers(app, window, work, record):
    from analysis_matrix import run as matrix
    from tests.e2e.analysis_result_checks import check_report
    from tests.e2e.header_geometry import check_headers, check_forest_footer
    pairs = (
        ("Drug", "Control"),
        ("Cognitive behavioural therapy plus usual care", "Usual care only"),
        ("Intensive individualized cognitive behavioural therapy plus structured clinical follow-up", "Standard clinical care"),
        ("Intensive individualized cognitive behavioural therapy plus structured clinical follow-up", "Intensive individualized cognitive behavioural therapy plus structured clinical follow-through"),
    )
    for names in pairs:
        for style in ('default', 'revman', 'bmj'):
            window.workspace.mark_saved()
            view = matrix(app, window, 'analysis-data-twoarm-proportion', record,
                          keep_results=True, parameters={'digits': 6, 'fp_style': style}, group_names=names)
            check_report(app, view, work, record)
            title, path = next(iter(view.results.display_images.items()))
            export = work / ('headers-' + style + '-' + str(len(names[0])) + '-' + str(len(names[1])) + '.svg')
            view.plot_service.export(regenerator='forest', params_path=view.params_paths[title], output_path=str(export))
            record('wrapped-arm-header-before-assertion', view, style=style, names=names,
                   plots={title:path}, export=str(export))
            measurements = [measurement for source in (path, str(export))
                            for measurement in (check_headers(source, names) + check_forest_footer(source, expected_directions=tuple("Favours " + name for name in names)))]
            if len(names[0]) > 80:
                from advanced_workflows import export_formats
                export_formats(app, view, work / ('headers-' + style + '-' + str(len(names[1]))),
                               'full-arm', record)
            view.report_action.setChecked(False)
            view._show_report(False)
            app.processEvents()
            record('measured-wrapped-arm-headers', view, style=style, names=names,
                   header_blocks=measurements, plots={title:path}, export=str(export))
            view.close()
