# Failed attempts (verbatim)

## baseline-tiny-sd-focused

Command: `uv run python scripts/verify_rcms.py calculator-mode-continuous-metrics --native`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "calculator-mode-continuous-metrics", "--native"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110013Z-6a0c0649-calculator-mode-continuous-metrics
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 83, in ready
    drive(dialog)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1115, in drive
    assert actual == expected, ("raw precision lost", mode, value, actual)
           ^^^^^^^^^^^^^^^^^^
AssertionError: ('raw precision lost', 'continuous-metrics', '0.00001', 0.0)
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 769, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1776, in run
    calculators(app, window, scenario.removeprefix("calculator-mode-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1180, in calculators
    modal(app, kind, drive, launch)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 97, in modal
    assert not errors, errors
           ^^^^^^^^^^
AssertionError: [AssertionError(('raw precision lost', 'continuous-metrics', '0.00001', 0.0))]
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 769, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1776, in run
    calculators(app, window, scenario.removeprefix("calculator-mode-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1180, in calculators
    modal(app, kind, drive, launch)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 97, in modal
    assert not errors, errors
           ^^^^^^^^^^
AssertionError: [AssertionError(('raw precision lost', 'continuous-metrics', '0.00001', 0.0))]


```

## baseline-tiny-sd

Command: `uv run python scripts/verify_rcms.py calculator-mode-continuous-metrics --native`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "calculator-mode-continuous-metrics", "--native"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T105938Z-0f4888f8-calculator-mode-continuous-metrics
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 83, in ready
    drive(dialog)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1115, in drive
    assert actual == expected, ("raw precision lost", mode, value, actual)
           ^^^^^^^^^^^^^^^^^^
AssertionError: ('raw precision lost', 'continuous-metrics', '0.00001', 22.0)
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 769, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1776, in run
    calculators(app, window, scenario.removeprefix("calculator-mode-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1180, in calculators
    modal(app, kind, drive, launch)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 97, in modal
    assert not errors, errors
           ^^^^^^^^^^
AssertionError: [AssertionError(('raw precision lost', 'continuous-metrics', '0.00001', 22.0))]
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 769, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1776, in run
    calculators(app, window, scenario.removeprefix("calculator-mode-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1180, in calculators
    modal(app, kind, drive, launch)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 97, in modal
    assert not errors, errors
           ^^^^^^^^^^
AssertionError: [AssertionError(('raw precision lost', 'continuous-metrics', '0.00001', 22.0))]


```

## calculator-boundary-replay

Command: `uv run python -m pytest tests/python/fast/test_calculator_qt6.py -q`

```text
["uv", "run", "python", "-m", "pytest", "tests/python/fast/test_calculator_qt6.py", "-q"]
............................F                                            [100%]
=================================== FAILURES ===================================
________ test_continuous_calculator_grid_columns_keep_internal_overflow ________

qapp = <PyQt6.QtWidgets.QApplication object at 0x7263a3154670>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7263a0a408d0>

    def test_continuous_calculator_grid_columns_keep_internal_overflow(qapp, monkeypatch):
        from rc_metastudio import continuous_data_dialog
    
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "get_confidence_multiplier_from_r",
            lambda conf: 1.96,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "continuous_convert_scale",
            lambda x, *args, **kwargs: x,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "impute_continuous_data",
            lambda data, alpha: {"succeeded": False, "comment": "stub"},
        )
    
        form = continuous_data_dialog.ContinuousDataDialog(
            FakeContinuousAnalysisUnit(),
            ["Group 1", "Group 2"],
            "Group 1-Group 2",
            "ROM",
            confidence_level=95.0,
        )
    
        form.resize(360, form.height())
        form.show()
        qapp.processEvents()
        table = _required(form.simple_table)
        header = _required(table.horizontalHeader())
        assert header.sectionResizeMode(0) == QHeaderView.ResizeMode.Interactive
        assert not header.stretchLastSection()
        assert (
            table.horizontalScrollBarPolicy() == QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
>       assert (
            sum(header.sectionSize(column) for column in range(table.columnCount()))
            > table.viewport().width()
        )
E       assert 342 > 375
E        +  where 342 = sum(<generator object test_continuous_calculator_grid_columns_keep_internal_overflow.<locals>.<genexpr> at 0x7263a0c5c4a0>)
E        +  and   375 = <built-in method width of QWidget object at 0x7263a0a2d3f0>()
E        +    where <built-in method width of QWidget object at 0x7263a0a2d3f0> = <PyQt6.QtWidgets.QWidget object at 0x7263a0a2d3f0>.width
E        +      where <PyQt6.QtWidgets.QWidget object at 0x7263a0a2d3f0> = <built-in method viewport of QTableWidget object at 0x7263a0a2eef0>()
E        +        where <built-in method viewport of QTableWidget object at 0x7263a0a2eef0> = <PyQt6.QtWidgets.QTableWidget object at 0x7263a0a2eef0>.viewport

tests/python/fast/test_calculator_qt6.py:1308: AssertionError
----------------------------- Captured stderr call -----------------------------
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
=========================== short test summary info ============================
FAILED tests/python/fast/test_calculator_qt6.py::test_continuous_calculator_grid_columns_keep_internal_overflow
1 failed, 28 passed in 1.18s

```

## calculator-existing-boundary-tests

Command: `uv run python -m pytest tests/python/fast/test_calculator_qt6.py -q`

```text
["uv", "run", "python", "-m", "pytest", "tests/python/fast/test_calculator_qt6.py", "-q"]
.............F..F...FF......FF                                           [100%]
=================================== FAILURES ===================================
__________ test_continuous_imputation_uses_r_keys_not_visible_headers __________

qapp = <PyQt6.QtWidgets.QApplication object at 0x7fc181d385e0>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7fc17f9c2d10>

    def test_continuous_imputation_uses_r_keys_not_visible_headers(qapp, monkeypatch):
        from rc_metastudio import continuous_data_dialog
    
        captured = []
    
        def fake_impute_continuous_data(params, alpha):
            captured.append(params.copy())
            return {"succeeded": False}
    
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "impute_continuous_data",
            fake_impute_continuous_data,
        )
    
        form = continuous_data_dialog.ContinuousDataDialog.__new__(
            continuous_data_dialog.ContinuousDataDialog
        )
        form.simple_table = QTableWidget(2, 8)
        form.simple_table.setHorizontalHeaderLabels(
            ["N", "Mean", "SD", "SE", "Variance", "Lower", "Upper", "P-Value"]
        )
        form.current_groups = ["Group 1", "Group 2"]
        form.confidence_level = 95.0
        form.analysis_unit = object()
        from rc_metastudio.calculator_service import CalculatorService
    
        form.calculator = CalculatorService()
    
        form.simple_table.setItem(0, 0, QTableWidgetItem("10"))
        form.simple_table.setItem(0, 1, QTableWidgetItem("94"))
        form.simple_table.setItem(0, 4, QTableWidgetItem("2.5"))
        form.simple_table.setItem(0, 5, QTableWidgetItem("90"))
        form.simple_table.setItem(0, 6, QTableWidgetItem("98"))
    
        form.impute_data()
    
>       assert captured[0] == {
            "n": 10.0,
            "mean": 94.0,
            "var": 2.5,
            "low": 90.0,
            "high": 98.0,
        }
E       AssertionError: assert {} == {'n': 10.0, '...w': 90.0, ...}
E         
E         Right contains 5 more items:
E         {'high': 98.0, 'low': 90.0, 'mean': 94.0, 'n': 10.0, 'var': 2.5}
E         Use -v to get more diff

tests/python/fast/test_calculator_qt6.py:484: AssertionError
_________ test_continuous_prepost_only_publishes_complete_differences __________

qapp = <PyQt6.QtWidgets.QApplication object at 0x7fc181d385e0>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7fc17f6c9050>

    def test_continuous_prepost_only_publishes_complete_differences(qapp, monkeypatch):
        from rc_metastudio import analysis_dataset, continuous_data_dialog, meta_globals
    
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "get_confidence_multiplier_from_r",
            lambda _confidence_level: 1.96,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "continuous_convert_scale",
            lambda value, *_args, **_kwargs: value,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "impute_continuous_data",
            lambda _data, _alpha: {"succeeded": False, "comment": "stub"},
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "back_calculate_continuous_data",
            lambda *_args, **_kwargs: {"FAIL": True},
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "continuous_effect_for_study",
            lambda *_args, **_kwargs: {"calc_scale": (-0.5, -1.0, 0.0)},
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "effect_triplet",
            lambda result, scale, metric=None: result[scale],
        )
    
        def values(n=None, mean=None, sd=None):
            return {
                "n": n,
                "mean": mean,
                "sd": sd,
                "se": None,
                "var": None,
                "low": None,
                "high": None,
                "pval": None,
            }
    
        def prepost(data, _correlation, _alpha):
            complete = all(
                data.get(field) is not None
                for field in ("n.A", "mean.A", "sd.A", "n.B", "mean.B", "sd.B")
            )
            if not complete:
                return {
                    "succeeded": True,
                    "output": values(),
                    "pre": values(),
                    "post": values(),
                }
            return {
                "succeeded": True,
                "output": values(60, -2, 29.7321),
                "pre": values(60, 94, 22),
                "post": values(60, 92, 20),
            }
    
        monkeypatch.setattr(
            calculator_service.r_bridge, "impute_pre_post_continuous_data", prepost
        )
        unit = analysis_dataset.AnalysisUnit(
            analysis_dataset.Outcome("Outcome", meta_globals.CONTINUOUS),
            raw_data=[[None, None, None], [60, 92, 20]],
            group_names=["Group 1", "Group 2"],
        )
        unit.set_effect_for_source(
            "entered", "SMD", "Group 1-Group 2", 0.0945, -0.1, 0.29
        )
        dialog = continuous_data_dialog.ContinuousDataDialog(
            unit,
            ["Group 1", "Group 2"],
            "Group 1-Group 2",
            "SMD",
            confidence_level=95.0,
        )
        for row, values_for_row in enumerate(((60, 94, 22), (60, 92, 20))):
            for column, value in enumerate(values_for_row):
                dialog._set_val(row, column, value, dialog.g1_pre_post_table)
    
        dialog.impute_pre_post_data(dialog.g1_pre_post_table, 0)
    
>       assert unit.get_raw_data_for_group("Group 1") == [60, -2, 29.7321]
E       assert [None, None, None] == [60, -2, 29.7321]
E         
E         At index 0 diff: None != 60
E         Use -v to get more diff

tests/python/fast/test_calculator_qt6.py:760: AssertionError
_ test_binary_calculator_table_layout_uses_real_headers_and_visible_total_row __

qapp = <PyQt6.QtWidgets.QApplication object at 0x7fc181d385e0>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7fc17f73c410>

    def test_binary_calculator_table_layout_uses_real_headers_and_visible_total_row(
        qapp, monkeypatch
    ):
        from rc_metastudio import binary_data_dialog
    
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "get_confidence_multiplier_from_r",
            lambda conf: 1.96,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "binary_convert_scale",
            lambda x, *args, **kwargs: x,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "impute_binary_data",
            lambda data: {"FAIL": True},
        )
    
        form = binary_data_dialog.BinaryDataDialog(
            FakeAnalysisUnit(),
            ["Group 1", "Group 2"],
            "Group 1-Group 2",
            "OR",
            confidence_level=95.0,
        )
    
        table = _required(form.raw_data_table)
    
>       assert form.event_lbl_3.isHidden()
               ^^^^^^^^^^^^^^^^
E       AttributeError: 'BinaryDataDialog' object has no attribute 'event_lbl_3'

tests/python/fast/test_calculator_qt6.py:889: AttributeError
__________ test_calculator_effect_ci_fields_fit_valid_domain_samples ___________

qapp = <PyQt6.QtWidgets.QApplication object at 0x7fc181d385e0>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7fc17f44c5d0>

    def test_calculator_effect_ci_fields_fit_valid_domain_samples(qapp, monkeypatch):
        from rc_metastudio import binary_data_dialog
        from rc_metastudio import continuous_data_dialog
        from rc_metastudio import diagnostic_data_dialog
    
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "get_confidence_multiplier_from_r",
            lambda conf: 1.96,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "binary_convert_scale",
            lambda x, *args, **kwargs: x,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "impute_binary_data",
            lambda data: {"FAIL": True},
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "get_confidence_multiplier_from_r",
            lambda conf: 1.96,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "continuous_convert_scale",
            lambda x, *args, **kwargs: x,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "impute_continuous_data",
            lambda data, alpha: {"succeeded": False, "comment": "stub"},
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "get_confidence_multiplier_from_r",
            lambda conf: 1.96,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "diagnostic_convert_scale",
            lambda x, *args, **kwargs: x,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "impute_diagnostic_data",
            lambda data: {"TP": None, "FP": None, "FN": None, "TN": None},
        )
    
        forms_and_representatives = [
            (
                binary_data_dialog.BinaryDataDialog(
                    FakeAnalysisUnit(),
                    ["Group 1", "Group 2"],
                    "Group 1-Group 2",
                    "OR",
                    confidence_level=95.0,
                ),
                "-0.8888",
            ),
            (
>               continuous_data_dialog.ContinuousDataDialog(
                    FakeContinuousAnalysisUnit(),
                    ["Group 1", "Group 2"],
                    "Group 1-Group 2",
                    "ROM",
                    confidence_level=95.0,
                ),
                "-0.8888",
            ),
            (
                diagnostic_data_dialog.DiagnosticDataDialog(
                    FakeDiagnosticAnalysisUnit(),
                    ["Group 1", "Group 2"],
                    "Group 1-Group 2",
                    confidence_level=95.0,
                ),
                "1.0000",
            ),
        ]

tests/python/fast/test_calculator_qt6.py:965: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <rc_metastudio.continuous_data_dialog.ContinuousDataDialog object at 0x7fc17f6bfe20>
analysis_unit = <test_calculator_qt6.FakeContinuousAnalysisUnit object at 0x7fc17f44c490>
current_groups = ['Group 1', 'Group 2'], group_comparison = 'Group 1-Group 2'
current_effect = 'ROM', confidence_level = 95.0, calculator = None
parent = None

    def __init__(
        self,
        analysis_unit,
        current_groups,
        group_comparison,
        current_effect,
        confidence_level=None,
        calculator: CalculatorService | None = None,
        parent=None,
    ):
        super(ContinuousDataDialog, self).__init__(parent)
        self.setupUi(self)
        self._configure_tables()
        self._configure_semantic_fields()
        self._configure_focus_revelation()
        self._layout_controller = adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )
        self.setup_signals_and_slots()
    
        if confidence_level is None:
            QMessageBox.critical(
                self, "Insufficient Arguments", "Confidence interval must be specified"
            )
            raise ValueError("Confidence interval must be specified")
        self.confidence_level = confidence_level
        self.calculator = calculator or CalculatorService()
        self.confidence_multiplier = self.calculator.get_confidence_multiplier(
            self.confidence_level
        )
    
        self.analysis_unit = analysis_unit
        self.current_groups = current_groups
        self.current_effect = current_effect
        self.group_comparison = group_comparison
        self.metric_parameter = None
        self.entry_widgets = [
            self.simple_table,
            self.g1_pre_post_table,
            self.g2_pre_post_table,
            self.effect_text_box,
            self.lower_text_box,
            self.upper_text_box,
            self.correlation_pre_post,
        ]
        self.text_boxes = [
            self.lower_text_box,
            self.upper_text_box,
            self.effect_text_box,
            self.correlation_pre_post,
        ]
        self.ci_label.setText(
            f"{self.confidence_level:g}% confidence interval"
        )
        self._configure_readable_ci_label()
        self.current_item_data = {}
    
        groups_names = [str(group_name) for group_name in self.current_groups]
        self.simple_table.setVerticalHeaderLabels(groups_names)
    
        self.tables = [
            self.simple_table,
            self.g1_pre_post_table,
            self.g2_pre_post_table,
        ]
        self.group_one_label.setText(str(self.current_groups[0]))
        self.group_two_label.setText(str(self.current_groups[1]))
        for table, group in zip((self.g1_pre_post_table, self.g2_pre_post_table), self.current_groups):
            table.setAccessibleName(f"{group} pre/post summaries")
            table.setAccessibleDescription(f"Pre-treatment and post-treatment summary values for {group}.")
    
        self.setup_clear_button_palettes()  # Color for clear_button_pallette
        self.initialize_form()  # initialize cells to empty items
        self._field_history = calc_fncs.TransientEditHistory()
    
        self.update_raw_data()
        self._populate_effect_data()
        self.set_current_effect()
        self.impute_data()
        self.update_effect_from_raw_data()
        self.update_back_calculation_button()
    
>       if self.analysis_unit.outcome.sub_type not in {"reg_coef", "generic_effect"}:
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'FakeContinuousAnalysisUnit' object has no attribute 'outcome'

src/rc_metastudio/continuous_data_dialog.py:181: AttributeError
________ test_continuous_calculator_grid_columns_keep_internal_overflow ________

qapp = <PyQt6.QtWidgets.QApplication object at 0x7fc181d385e0>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7fc17f9b9750>

    def test_continuous_calculator_grid_columns_keep_internal_overflow(qapp, monkeypatch):
        from rc_metastudio import continuous_data_dialog
    
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "get_confidence_multiplier_from_r",
            lambda conf: 1.96,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "continuous_convert_scale",
            lambda x, *args, **kwargs: x,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "impute_continuous_data",
            lambda data, alpha: {"succeeded": False, "comment": "stub"},
        )
    
>       form = continuous_data_dialog.ContinuousDataDialog(
            FakeContinuousAnalysisUnit(),
            ["Group 1", "Group 2"],
            "Group 1-Group 2",
            "ROM",
            confidence_level=95.0,
        )

tests/python/fast/test_calculator_qt6.py:1287: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <rc_metastudio.continuous_data_dialog.ContinuousDataDialog object at 0x7fc17f762b00>
analysis_unit = <test_calculator_qt6.FakeContinuousAnalysisUnit object at 0x7fc17f9b9690>
current_groups = ['Group 1', 'Group 2'], group_comparison = 'Group 1-Group 2'
current_effect = 'ROM', confidence_level = 95.0, calculator = None
parent = None

    def __init__(
        self,
        analysis_unit,
        current_groups,
        group_comparison,
        current_effect,
        confidence_level=None,
        calculator: CalculatorService | None = None,
        parent=None,
    ):
        super(ContinuousDataDialog, self).__init__(parent)
        self.setupUi(self)
        self._configure_tables()
        self._configure_semantic_fields()
        self._configure_focus_revelation()
        self._layout_controller = adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )
        self.setup_signals_and_slots()
    
        if confidence_level is None:
            QMessageBox.critical(
                self, "Insufficient Arguments", "Confidence interval must be specified"
            )
            raise ValueError("Confidence interval must be specified")
        self.confidence_level = confidence_level
        self.calculator = calculator or CalculatorService()
        self.confidence_multiplier = self.calculator.get_confidence_multiplier(
            self.confidence_level
        )
    
        self.analysis_unit = analysis_unit
        self.current_groups = current_groups
        self.current_effect = current_effect
        self.group_comparison = group_comparison
        self.metric_parameter = None
        self.entry_widgets = [
            self.simple_table,
            self.g1_pre_post_table,
            self.g2_pre_post_table,
            self.effect_text_box,
            self.lower_text_box,
            self.upper_text_box,
            self.correlation_pre_post,
        ]
        self.text_boxes = [
            self.lower_text_box,
            self.upper_text_box,
            self.effect_text_box,
            self.correlation_pre_post,
        ]
        self.ci_label.setText(
            f"{self.confidence_level:g}% confidence interval"
        )
        self._configure_readable_ci_label()
        self.current_item_data = {}
    
        groups_names = [str(group_name) for group_name in self.current_groups]
        self.simple_table.setVerticalHeaderLabels(groups_names)
    
        self.tables = [
            self.simple_table,
            self.g1_pre_post_table,
            self.g2_pre_post_table,
        ]
        self.group_one_label.setText(str(self.current_groups[0]))
        self.group_two_label.setText(str(self.current_groups[1]))
        for table, group in zip((self.g1_pre_post_table, self.g2_pre_post_table), self.current_groups):
            table.setAccessibleName(f"{group} pre/post summaries")
            table.setAccessibleDescription(f"Pre-treatment and post-treatment summary values for {group}.")
    
        self.setup_clear_button_palettes()  # Color for clear_button_pallette
        self.initialize_form()  # initialize cells to empty items
        self._field_history = calc_fncs.TransientEditHistory()
    
        self.update_raw_data()
        self._populate_effect_data()
        self.set_current_effect()
        self.impute_data()
        self.update_effect_from_raw_data()
        self.update_back_calculation_button()
    
>       if self.analysis_unit.outcome.sub_type not in {"reg_coef", "generic_effect"}:
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'FakeContinuousAnalysisUnit' object has no attribute 'outcome'

src/rc_metastudio/continuous_data_dialog.py:181: AttributeError
_________ test_continuous_calculator_keeps_long_imputed_values_compact _________

qapp = <PyQt6.QtWidgets.QApplication object at 0x7fc181d385e0>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7fc17f7690d0>

    def test_continuous_calculator_keeps_long_imputed_values_compact(qapp, monkeypatch):
        from rc_metastudio import continuous_data_dialog
    
        long_imputed = {
            "n": 10,
            "mean": 92.89482413483651,
            "sd": 2.604729426373378,
            "se": 8.75360686626884e-310,
            "var": 3.4972319657703745e-249,
            "pval": 0.12345678912345678,
            "low": 91.11111111111111,
            "high": 94.99999999999999,
        }
    
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "get_confidence_multiplier_from_r",
            lambda conf: 1.96,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "continuous_convert_scale",
            lambda x, *args, **kwargs: x,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "impute_continuous_data",
            lambda data, alpha: {"succeeded": True, "output": long_imputed},
        )
    
>       form = continuous_data_dialog.ContinuousDataDialog(
            FakeContinuousAnalysisUnit(),
            ["Group 1", "Group 2"],
            "Group 1-Group 2",
            "ROM",
            confidence_level=95.0,
        )

tests/python/fast/test_calculator_qt6.py:1341: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <rc_metastudio.continuous_data_dialog.ContinuousDataDialog object at 0x7fc17f7629e0>
analysis_unit = <test_calculator_qt6.FakeContinuousAnalysisUnit object at 0x7fc17f768890>
current_groups = ['Group 1', 'Group 2'], group_comparison = 'Group 1-Group 2'
current_effect = 'ROM', confidence_level = 95.0, calculator = None
parent = None

    def __init__(
        self,
        analysis_unit,
        current_groups,
        group_comparison,
        current_effect,
        confidence_level=None,
        calculator: CalculatorService | None = None,
        parent=None,
    ):
        super(ContinuousDataDialog, self).__init__(parent)
        self.setupUi(self)
        self._configure_tables()
        self._configure_semantic_fields()
        self._configure_focus_revelation()
        self._layout_controller = adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )
        self.setup_signals_and_slots()
    
        if confidence_level is None:
            QMessageBox.critical(
                self, "Insufficient Arguments", "Confidence interval must be specified"
            )
            raise ValueError("Confidence interval must be specified")
        self.confidence_level = confidence_level
        self.calculator = calculator or CalculatorService()
        self.confidence_multiplier = self.calculator.get_confidence_multiplier(
            self.confidence_level
        )
    
        self.analysis_unit = analysis_unit
        self.current_groups = current_groups
        self.current_effect = current_effect
        self.group_comparison = group_comparison
        self.metric_parameter = None
        self.entry_widgets = [
            self.simple_table,
            self.g1_pre_post_table,
            self.g2_pre_post_table,
            self.effect_text_box,
            self.lower_text_box,
            self.upper_text_box,
            self.correlation_pre_post,
        ]
        self.text_boxes = [
            self.lower_text_box,
            self.upper_text_box,
            self.effect_text_box,
            self.correlation_pre_post,
        ]
        self.ci_label.setText(
            f"{self.confidence_level:g}% confidence interval"
        )
        self._configure_readable_ci_label()
        self.current_item_data = {}
    
        groups_names = [str(group_name) for group_name in self.current_groups]
        self.simple_table.setVerticalHeaderLabels(groups_names)
    
        self.tables = [
            self.simple_table,
            self.g1_pre_post_table,
            self.g2_pre_post_table,
        ]
        self.group_one_label.setText(str(self.current_groups[0]))
        self.group_two_label.setText(str(self.current_groups[1]))
        for table, group in zip((self.g1_pre_post_table, self.g2_pre_post_table), self.current_groups):
            table.setAccessibleName(f"{group} pre/post summaries")
            table.setAccessibleDescription(f"Pre-treatment and post-treatment summary values for {group}.")
    
        self.setup_clear_button_palettes()  # Color for clear_button_pallette
        self.initialize_form()  # initialize cells to empty items
        self._field_history = calc_fncs.TransientEditHistory()
    
        self.update_raw_data()
        self._populate_effect_data()
        self.set_current_effect()
        self.impute_data()
        self.update_effect_from_raw_data()
        self.update_back_calculation_button()
    
>       if self.analysis_unit.outcome.sub_type not in {"reg_coef", "generic_effect"}:
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'FakeContinuousAnalysisUnit' object has no attribute 'outcome'

src/rc_metastudio/continuous_data_dialog.py:181: AttributeError
=========================== short test summary info ============================
FAILED tests/python/fast/test_calculator_qt6.py::test_continuous_imputation_uses_r_keys_not_visible_headers
FAILED tests/python/fast/test_calculator_qt6.py::test_continuous_prepost_only_publishes_complete_differences
FAILED tests/python/fast/test_calculator_qt6.py::test_binary_calculator_table_layout_uses_real_headers_and_visible_total_row
FAILED tests/python/fast/test_calculator_qt6.py::test_calculator_effect_ci_fields_fit_valid_domain_samples
FAILED tests/python/fast/test_calculator_qt6.py::test_continuous_calculator_grid_columns_keep_internal_overflow
FAILED tests/python/fast/test_calculator_qt6.py::test_continuous_calculator_keeps_long_imputed_values_compact
6 failed, 24 passed in 1.17s

```

## calculator-native-all

Command: `bash -c for mode in continuous-metrics onearm-mean pre-post back-continuous entered-continuous binary-metrics diagnostic-metrics onearm-proportion entered-binary entered-diagnostic back-binary back-diagnostic; do uv run python scripts/verify_rcms.py "calculator-mode-$mode" --native || exit; done`

```text
["bash", "-c", "for mode in continuous-metrics onearm-mean pre-post back-continuous entered-continuous binary-metrics diagnostic-metrics onearm-proportion entered-binary entered-diagnostic back-binary back-diagnostic; do uv run python scripts/verify_rcms.py \"calculator-mode-$mode\" --native || exit; done"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110156Z-829d7b2a-calculator-mode-continuous-metrics
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110214Z-fa64e8bc-calculator-mode-onearm-mean
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110240Z-46be4972-calculator-mode-pre-post
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110301Z-80aba4ef-calculator-mode-back-continuous
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110320Z-66493949-calculator-mode-entered-continuous
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110336Z-8b35f8ff-calculator-mode-binary-metrics
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110358Z-46ece6a5-calculator-mode-diagnostic-metrics
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110432Z-a993ed9b-calculator-mode-onearm-proportion
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 84, in ready
    drive(dialog)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1102, in drive
    cell(table, 0, column, float(table.item(0, column).text()) + 1)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 806, in cell
    assert editor is not None, (mode, row, column)
           ^^^^^^^^^^^^^^^^^^
AssertionError: ('onearm-proportion', 0, 0)
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1786, in run
    calculators(app, window, scenario.removeprefix("calculator-mode-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1186, in calculators
    modal(app, kind, drive, launch)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 98, in modal
    assert not errors, errors
           ^^^^^^^^^^
AssertionError: [AssertionError(('onearm-proportion', 0, 0))]
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1786, in run
    calculators(app, window, scenario.removeprefix("calculator-mode-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1186, in calculators
    modal(app, kind, drive, launch)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 98, in modal
    assert not errors, errors
           ^^^^^^^^^^
AssertionError: [AssertionError(('onearm-proportion', 0, 0))]


```

## golden-before-refresh

Command: `uv run python scripts/verify_golden_compatibility.py --output-root build/qt6-verification/golden-round6`

```text
["uv", "run", "python", "scripts/verify_golden_compatibility.py", "--output-root", "build/qt6-verification/golden-round6"]
Golden compatibility verification failed: Golden output must use a dedicated golden-compatibility directory

```

## golden-presentation-capture

Command: `uv run python scripts/verify_golden_compatibility.py --output-root build/qt6-verification/golden-compatibility-round6`

```text
["uv", "run", "python", "scripts/verify_golden_compatibility.py", "--output-root", "build/qt6-verification/golden-compatibility-round6"]
{
  "baseline": "tests/analysis_regression/baseline/observed-golden-baseline.zip",
  "capture_passed": true,
  "case_count": 11,
  "comparison": {
    "passed": false,
    "rows": [
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.calculation_scale.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.calculation_scale.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.calculation_scale.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.calculation_scale.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.heterogeneity_df matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.heterogeneity_p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.i_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.q matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.tau_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.de_vries matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.giamarellou matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.gonzalez matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.hansen matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.hollender matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.klastersky matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.maller matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.marik matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.mauracher matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.muijsken matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.nordstrom matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.prins matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.rozdzinski matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.sturm matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.ter_braak matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.tulkens matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.van_der_auwera matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.vanhaeverbeek matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.vigano matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section References matched.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section Summary matched.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section Weights matched.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "amino.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Artifact Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.heterogeneity_df matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.heterogeneity_p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.i_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.q matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.tau_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.carroll matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.donat matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.grant matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.peck matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.stewart matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.young matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section References matched.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section Summary matched.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section Weights matched.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "accepted_exception",
        "dataset": "continuous.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Artifact Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.calculation_scale.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.calculation_scale.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.calculation_scale.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.calculation_scale.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.heterogeneity_df matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.heterogeneity_p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.i_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.q matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.study_count matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.tau_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Text section Odds Ratio Summary matched.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Text section References matched.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "lymph.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Artifact Odds Ratio Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.gonzalez.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.gonzalez.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.gonzalez.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.gonzalez.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_de_vries.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_de_vries.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_de_vries.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_de_vries.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_de_vries.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_giamarellou.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_giamarellou.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_giamarellou.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_giamarellou.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_giamarellou.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hansen.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hansen.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hansen.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hansen.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hansen.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hollender.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hollender.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hollender.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hollender.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hollender.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_klastersky.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_klastersky.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_klastersky.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_klastersky.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_klastersky.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_maller.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_maller.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_maller.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_maller.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_maller.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_marik.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_marik.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_marik.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_marik.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_marik.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_mauracher.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_mauracher.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_mauracher.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_mauracher.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_mauracher.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_muijsken.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_muijsken.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_muijsken.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_muijsken.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_muijsken.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_nordstrom.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_nordstrom.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_nordstrom.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_nordstrom.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_nordstrom.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_prins.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_prins.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_prins.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_prins.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_prins.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_rozdzinski.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_rozdzinski.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_rozdzinski.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_rozdzinski.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_rozdzinski.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_sturm.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_sturm.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_sturm.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_sturm.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_sturm.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_ter_braak.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_ter_braak.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_ter_braak.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_ter_braak.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_ter_braak.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_tulkens.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_tulkens.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_tulkens.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_tulkens.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_tulkens.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_van_der_auwera.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_van_der_auwera.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_van_der_auwera.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_van_der_auwera.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_van_der_auwera.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vanhaeverbeek.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vanhaeverbeek.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vanhaeverbeek.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vanhaeverbeek.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vanhaeverbeek.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vigano.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vigano.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vigano.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vigano.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vigano.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "text_artifact_drift",
        "dataset": "amino.rcms",
        "detail": "Text section Cumulative Summary changed.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section References matched.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "amino.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Artifact Cumulative Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.overall.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.overall.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.overall.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.overall.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.overall.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_de_vries.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_de_vries.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_de_vries.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_de_vries.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_de_vries.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_giamarellou.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_giamarellou.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_giamarellou.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_giamarellou.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_giamarellou.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_gonzalez.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_gonzalez.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_gonzalez.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_gonzalez.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_gonzalez.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hansen.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hansen.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hansen.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hansen.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hansen.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hollender.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hollender.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hollender.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hollender.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hollender.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_klastersky.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_klastersky.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_klastersky.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_klastersky.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_klastersky.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_maller.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_maller.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_maller.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_maller.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_maller.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_marik.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_marik.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_marik.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_marik.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_marik.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_mauracher.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_mauracher.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_mauracher.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_mauracher.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_mauracher.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_muijsken.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_muijsken.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_muijsken.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_muijsken.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_muijsken.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_nordstrom.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_nordstrom.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_nordstrom.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_nordstrom.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_nordstrom.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_prins.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_prins.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_prins.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_prins.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_prins.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_rozdzinski.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_rozdzinski.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_rozdzinski.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_rozdzinski.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_rozdzinski.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_sturm.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_sturm.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_sturm.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_sturm.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_sturm.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_ter_braak.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_ter_braak.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_ter_braak.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_ter_braak.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_ter_braak.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_tulkens.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_tulkens.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_tulkens.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_tulkens.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_tulkens.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_van_der_auwera.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_van_der_auwera.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_van_der_auwera.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_van_der_auwera.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_van_der_auwera.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vanhaeverbeek.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vanhaeverbeek.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vanhaeverbeek.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vanhaeverbeek.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vanhaeverbeek.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vigano.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vigano.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vigano.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vigano.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vigano.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "text_artifact_drift",
        "dataset": "amino.rcms",
        "detail": "Text section Leave-one-out Summary changed.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section References matched.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "amino.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Artifact Leave-one-out Forest plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.carroll.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.carroll.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.carroll.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.carroll.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_donat.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_donat.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_donat.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_donat.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_donat.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_grant.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_grant.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_grant.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_grant.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_grant.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_peck.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_peck.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_peck.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_peck.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_peck.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_stewart.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_stewart.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_stewart.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_stewart.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_stewart.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_young.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_young.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_young.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_young.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_young.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section Cumulative Summary matched.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section References matched.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "accepted_exception",
        "dataset": "continuous.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Artifact Cumulative Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.overall.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.overall.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.overall.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.overall.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.overall.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_carroll.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_carroll.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_carroll.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_carroll.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_carroll.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_donat.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_donat.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_donat.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_donat.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_donat.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_grant.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_grant.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_grant.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_grant.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_grant.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_peck.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_peck.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_peck.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_peck.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_peck.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_stewart.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_stewart.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_stewart.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_stewart.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_stewart.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_young.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_young.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_young.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_young.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_young.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section Leave-one-out Summary matched.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section References matched.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "accepted_exception",
        "dataset": "continuous.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Artifact Leave-one-out Forest plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.golden_year.coefficient matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.golden_year.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.golden_year.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.golden_year.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.golden_year.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.intercept.coefficient matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.intercept.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.intercept.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.intercept.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.intercept.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.omnibus.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.de_vries matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.giamarellou matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.gonzalez matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.hansen matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.hollender matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.klastersky matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.maller matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.marik matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.mauracher matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.muijsken matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.nordstrom matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.prins matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.rozdzinski matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.sturm matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.ter_braak matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.tulkens matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.van_der_auwera matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.vanhaeverbeek matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.vigano matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section References matched.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "amino.rcms",
        "detail": "Text section Summary changed.",
        "exception": "PR #349 intentionally improves meta-regression summary and reference text.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section Weights matched.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "amino.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Artifact Regression Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.golden_year.coefficient matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.golden_year.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.golden_year.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.golden_year.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.golden_year.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.intercept.coefficient matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.intercept.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.intercept.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.intercept.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.intercept.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.omnibus.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.carroll matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.donat matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.grant matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.peck matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.stewart matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.young matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section References matched.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "accepted_exception",
        "dataset": "continuous.rcms",
        "detail": "Text section Summary changed.",
        "exception": "PR #349 intentionally improves meta-regression summary and reference text.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section Weights matched.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "accepted_exception",
        "dataset": "continuous.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Artifact Regression Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.overall.df matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.overall.i_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.overall.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.overall.q matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_early.df matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_early.i_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_early.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_early.q matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_late.df matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_late.i_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_late.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_late.q matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.studies matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.z_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.studies matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.z_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.studies matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.z_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section References matched.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "text_artifact_drift",
        "dataset": "amino.rcms",
        "detail": "Text section Subgroup Summary changed.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "amino.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Artifact Subgroup Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.overall.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.overall.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.overall.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.overall.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.overall.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section References matched.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section Subgroup Summary matched.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "accepted_exception",
        "dataset": "continuous.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Artifact Subgroups Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      }
    ]
  },
  "comparison_count": 474,
  "numeric_contract": {
    "metric_count": 415,
    "path": "tests/analysis_regression/baseline/numeric-contract.json",
    "sha256": "5a14768e2cc755b198646897a27efcd13369de08c5f556d9e5d444de98a65e8f"
  },
  "passed": false,
  "rpy2_identities": {
    "rpy2": "3.6.7",
    "rpy2-rinterface": "3.6.6",
    "rpy2-robjects": "3.6.5"
  }
}

```

## grid-precision-editors

Command: `uv run python scripts/verify_rcms.py calculator-grid-precision`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "calculator-grid-precision"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110521Z-5138de2a-calculator-grid-precision
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support raise()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
UNEXPECTED DIALOG: The higher CI must be greater than the point estimate!
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1765, in run
    precision(app, window, record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/precision_inputs.py", line 95, in run
    assert float(edit(row, column)) == expected[row]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1765, in run
    precision(app, window, record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/precision_inputs.py", line 95, in run
    assert float(edit(row, column)) == expected[row]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError


```

## grid-precision-first

Command: `uv run python scripts/verify_rcms.py calculator-grid-precision`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "calculator-grid-precision"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110305Z-4408bc9e-calculator-grid-precision
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    calculator(app, window, scenario.removeprefix("calculator-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 587, in calculator
    sample, dialog_type, table_name, column = {
                                              ^
KeyError: 'grid-precision'
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    calculator(app, window, scenario.removeprefix("calculator-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 587, in calculator
    sample, dialog_type, table_name, column = {
                                              ^
KeyError: 'grid-precision'


```

## grid-precision-routed

Command: `uv run python scripts/verify_rcms.py calculator-grid-precision`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "calculator-grid-precision"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110350Z-a3fe3620-calculator-grid-precision
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support raise()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1765, in run
    precision(app, window, record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/precision_inputs.py", line 94, in run
    edit(row, column, text)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/precision_inputs.py", line 26, in edit
    assert isinstance(editor, QtWidgets.QLineEdit), editor
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1765, in run
    precision(app, window, record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/precision_inputs.py", line 94, in run
    edit(row, column, text)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/precision_inputs.py", line 26, in edit
    assert isinstance(editor, QtWidgets.QLineEdit), editor
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None


```

## grid-precision-second

Command: `uv run python scripts/verify_rcms.py calculator-grid-precision`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "calculator-grid-precision"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110326Z-5737d139-calculator-grid-precision
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    calculator(app, window, scenario.removeprefix("calculator-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 587, in calculator
    sample, dialog_type, table_name, column = {
                                              ^
KeyError: 'grid-precision'
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    calculator(app, window, scenario.removeprefix("calculator-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 587, in calculator
    sample, dialog_type, table_name, column = {
                                              ^
KeyError: 'grid-precision'


```

## grid-precision-third

Command: `uv run python scripts/verify_rcms.py calculator-grid-precision`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "calculator-grid-precision"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110344Z-8e9899b7-calculator-grid-precision
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    elif scenario.startswith("calculator-"):
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 587, in calculator
    sample, dialog_type, table_name, column = {
                                              ^
KeyError: 'grid-precision'
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    elif scenario.startswith("calculator-"):
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 587, in calculator
    sample, dialog_type, table_name, column = {
                                              ^
KeyError: 'grid-precision'


```

## labels-expanded

Command: `uv run python scripts/verify_rcms.py project-display-labels`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "project-display-labels"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T111320Z-952d9adf-project-display-labels
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support raise()
This plugin does not support propagateSizeHints()
qt.gui.imageio: QImageIOHandler: Rejecting image as it exceeds the current allocation limit of 256 megabytes
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1791, in run
    labels(app, window, record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/display_labels.py", line 67, in run
    view = analyze_existing(app, window, 'standard', 'time_to_event.random' if family == 'hr' else 'event_rate.random', observe)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/audit_round3.py", line 410, in analyze_existing
    dialog.method_cbo_box.setCurrentText(next(label for label, key in dialog.available_method_d.items() if key == method))
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
StopIteration
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1791, in run
    labels(app, window, record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/display_labels.py", line 67, in run
    view = analyze_existing(app, window, 'standard', 'time_to_event.random' if family == 'hr' else 'event_rate.random', observe)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/audit_round3.py", line 410, in analyze_existing
    dialog.method_cbo_box.setCurrentText(next(label for label, key in dialog.available_method_d.items() if key == method))
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
StopIteration


```

## labels-first

Command: `uv run python scripts/verify_rcms.py project-display-labels`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "project-display-labels"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T111255Z-7916be2f-project-display-labels
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1791, in run
    labels(app, window, record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/display_labels.py", line 63, in run
    matrix(app, window, 'analysis-data-' + family, observe)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/analysis_matrix.py", line 357, in run
    assert not callback_errors, callback_errors
           ^^^^^^^^^^^^^^^^^^^
AssertionError: [AssertionError(('metric needs a readable name', 'twoarm_smds_Button', 'SMD'))]
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1791, in run
    labels(app, window, record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/display_labels.py", line 63, in run
    matrix(app, window, 'analysis-data-' + family, observe)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/analysis_matrix.py", line 357, in run
    assert not callback_errors, callback_errors
           ^^^^^^^^^^^^^^^^^^^
AssertionError: [AssertionError(('metric needs a readable name', 'twoarm_smds_Button', 'SMD'))]


```

## polish-native-first

Command: `bash -c for scenario in audit-round3-round5 audit-round3-arm-names analysis-diagnostic-regression-continuous project-shell; do uv run python scripts/verify_rcms.py "$scenario" --native || exit; done`

```text
["bash", "-c", "for scenario in audit-round3-round5 audit-round3-arm-names analysis-diagnostic-regression-continuous project-shell; do uv run python scripts/verify_rcms.py \"$scenario\" --native || exit; done"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T111318Z-b875900e-audit-round3-round5
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T111552Z-82a55d11-audit-round3-arm-names
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 735, in <module>
    run(app, window, WORK, record_step, scenario)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/audit_round3.py", line 508, in run
    return naming(app, window, work, record)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/arm_names.py", line 62, in run
    assert expected[0] in view.identity_label.text(), view.identity_label.text()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Meta-analysis — Verification outcome · Single-arm mean · Mean
Follow-up: first
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 735, in <module>
    run(app, window, WORK, record_step, scenario)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/audit_round3.py", line 508, in run
    return naming(app, window, work, record)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/arm_names.py", line 62, in run
    assert expected[0] in view.identity_label.text(), view.identity_label.text()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Meta-analysis — Verification outcome · Single-arm mean · Mean
Follow-up: first


```

## precision-and-contour-targeted

Command: `uv run python scripts/verify_rcms.py project-round6-polish`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "project-round6-polish"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T111906Z-ecb44b94-project-round6-polish
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 86, in ready
    drive(dialog)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/round6_polish.py", line 46, in small_study
    assert '10' in explanation and '9' in explanation, explanation
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: No formal asymmetry test is available.
Disabled by default below 10 usable studies.
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1812, in run
    polish(app, window, Path(sys.argv[2]), record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/round6_polish.py", line 59, in run
    modal(app, PublicationBiasDialog, small_study, window.action_publication_bias.trigger)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 100, in modal
    assert not errors, errors
           ^^^^^^^^^^
AssertionError: [AssertionError('No formal asymmetry test is available.\nDisabled by default below 10 usable studies.')]
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1812, in run
    polish(app, window, Path(sys.argv[2]), record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/round6_polish.py", line 59, in run
    modal(app, PublicationBiasDialog, small_study, window.action_publication_bias.trigger)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 100, in modal
    assert not errors, errors
           ^^^^^^^^^^
AssertionError: [AssertionError('No formal asymmetry test is available.\nDisabled by default below 10 usable studies.')]


```

## python-affected

Command: `uv run python -m pytest tests/python/fast tests/python/gui/test_diagnostic_transactional_layout.py -q`

```text
["uv", "run", "python", "-m", "pytest", "tests/python/fast", "tests/python/gui/test_diagnostic_transactional_layout.py", "-q"]
....................................................................F... [ 18%]
...................F....F............................................... [ 36%]
........................................................................ [ 55%]
..............................sss.............s.s....................... [ 73%]
....................................................s................... [ 91%]
......................F....FF...                                         [100%]
=================================== FAILURES ===================================
_____ test_rename_group_preserves_effects_when_the_name_contains_a_hyphen ______

    def test_rename_group_preserves_effects_when_the_name_contains_a_hyphen():
        dataset = _dataset(analysis_dataset.BINARY)
        unit = dataset.studies[0].analysis_units_by_outcome["Outcome"]["first"]
        original_groups = unit.get_group_names()
        dataset.change_group_name(original_groups[0], "Usual-care")
        pair_key = "-".join(("Usual-care", original_groups[1]))
        unit.entered_effects["OR"][pair_key]["est"] = 0.75
    
        dataset.change_group_name("Usual-care", "Control")
    
        renamed_key = "-".join(("Control", original_groups[1]))
        assert unit.get_group_names() == ["Control", original_groups[1]]
        assert unit.groups["Control"].name == "Control"
>       assert unit.entered_effects["OR"][renamed_key]["est"] == 0.75
E       assert None == 0.75

tests/python/fast/test_dataset_contracts.py:81: AssertionError
______ test_dataset_group_and_follow_up_order_is_stable_across_hash_seeds ______

    def test_dataset_group_and_follow_up_order_is_stable_across_hash_seeds():
        script = textwrap.dedent(
            """
            import json
            from rc_metastudio import analysis_dataset
            from rc_metastudio import meta_globals
    
            dataset = analysis_dataset.Dataset()
            outcome = analysis_dataset.Outcome("Mortality", meta_globals.BINARY)
            study = analysis_dataset.Study(1, "Alpha")
            dataset.add_study(study)
            dataset.add_outcome(outcome)
            dataset.add_group("tx C", "Mortality")
            dataset.add_group("tx D", "Mortality")
            dataset.change_follow_up_name("Mortality", "first", "baseline")
            dataset.add_follow_up_to_outcome("Mortality", "week 4")
            dataset.add_follow_up_to_outcome("Mortality", "week 8")
    
            print(json.dumps({
                "all_groups": dataset.get_group_names(),
                "fu_groups": dataset.get_group_names_for_outcome_follow_up(
                    "Mortality", "week 4"
                ),
                "follow_ups": dataset.get_follow_up_names(),
            }))
            """
        )
        expected = {
            "all_groups": ["tx A", "tx B", "tx C", "tx D"],
            "fu_groups": ["tx A", "tx B", "tx C", "tx D"],
            "follow_ups": ["baseline", "week 4", "week 8"],
        }
    
        for seed in ("1", "2"):
            env = os.environ.copy()
            env["PYTHONHASHSEED"] = seed
            env["PYTHONPATH"] = os.path.abspath("src")
            result = subprocess.run(
                [sys.executable, "-c", script],
                check=True,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
>           assert json.loads(result.stdout.splitlines()[-1]) == expected
E           AssertionError: assert {'all_groups'...4', 'week 8']} == {'all_groups'...4', 'week 8']}
E             
E             Omitting 1 identical items, use -vv to show
E             Differing items:
E             {'fu_groups': ['Intervention', 'Control', 'tx C', 'tx D']} != {'fu_groups': ['tx A', 'tx B', 'tx C', 'tx D']}
E             {'all_groups': ['Intervention', 'Control', 'tx C', 'tx D']} != {'all_groups': ['tx A', 'tx B', 'tx C', 'tx D']}
E             Use -v to get more diff

tests/python/fast/test_dataset_ordering.py:67: AssertionError
_____________ test_editable_labels_do_not_change_domain_identities _____________

    def test_editable_labels_do_not_change_domain_identities():
        dataset = analysis_dataset.Dataset()
        outcome = analysis_dataset.Outcome("Outcome", meta_globals.CONTINUOUS)
        study = analysis_dataset.Study(0, "Study")
        dataset.add_study(study)
        dataset.add_outcome(outcome)
        dataset.add_follow_up_to_outcome("Outcome", "week 2")
        unit = study.get_analysis_unit("Outcome", "week 2")
>       group_id = unit.groups["tx A"].stable_id
                   ^^^^^^^^^^^^^^^^^^^
E       KeyError: 'tx A'

tests/python/fast/test_domain_identity.py:14: KeyError
_________ test_large_font_count_overflow_and_focus_stay_inside_content _________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7d299c0aeb10>

    def test_large_font_count_overflow_and_focus_stay_inside_content(monkeypatch):
        app = cast(
            QtWidgets.QApplication,
            required(
                QtWidgets.QApplication.instance() or QtWidgets.QApplication([]),
                "application",
            ),
        )
        old_font = app.font()
        enlarged = QtGui.QFont(old_font)
        enlarged.setPointSize(max(16, old_font.pointSize() + 6))
        app.setFont(enlarged)
        app, dialog = _open_data_dialog(monkeypatch)
        try:
            dialog.show()
            dialog.resize(320, 300)
            app.processEvents()
            dialog.current_item_data = 12
            dialog.two_by_two_table.item(0, 0).setText("999999999999999999")
            app.processEvents()
    
            assert AVAILABLE.contains(dialog.frameGeometry())
>           assert dialog.two_by_two_table.horizontalScrollBar().maximum() > 0
E           assert 0 > 0
E            +  where 0 = <built-in method maximum of QScrollBar object at 0x7d299cd8e170>()
E            +    where <built-in method maximum of QScrollBar object at 0x7d299cd8e170> = <PyQt6.QtWidgets.QScrollBar object at 0x7d299cd8e170>.maximum
E            +      where <PyQt6.QtWidgets.QScrollBar object at 0x7d299cd8e170> = <built-in method horizontalScrollBar of QTableWidget object at 0x7d299cd8dcf0>()
E            +        where <built-in method horizontalScrollBar of QTableWidget object at 0x7d299cd8dcf0> = <PyQt6.QtWidgets.QTableWidget object at 0x7d299cd8dcf0>.horizontalScrollBar
E            +          where <PyQt6.QtWidgets.QTableWidget object at 0x7d299cd8dcf0> = <rc_metastudio.diagnostic_data_dialog.DiagnosticDataDialog object at 0x7d299cd8d3f0>.two_by_two_table

tests/python/gui/test_diagnostic_transactional_layout.py:337: AssertionError
----------------------------- Captured stderr call -----------------------------
This plugin does not support propagateSizeHints()
_ test_direct_effect_validation_is_complete_and_reachable_with_large_font[effect] _

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7d299c0b26d0>
field_name = 'effect_text_box', invalid_value = 'not numeric'
guidance = 'must be numeric', restored = '0.75'

    @pytest.mark.parametrize(
        ("field_name", "invalid_value", "guidance", "restored"),
        [
            ("effect_text_box", "not numeric", "must be numeric", "0.75"),
            ("lower_text_box", "0.95", "lower CI must be less", "0.6"),
        ],
        ids=["effect", "interval"],
    )
    def test_direct_effect_validation_is_complete_and_reachable_with_large_font(
        monkeypatch, field_name, invalid_value, guidance, restored
    ):
        from rc_metastudio import diagnostic_data_dialog
    
        app = cast(
            QtWidgets.QApplication,
            required(
                QtWidgets.QApplication.instance() or QtWidgets.QApplication([]),
                "application",
            ),
        )
        old_font = app.font()
        enlarged = QtGui.QFont(old_font)
        enlarged.setPointSize(max(16, old_font.pointSize() + 6))
        app.setFont(enlarged)
        app, dialog = _open_data_dialog(
            monkeypatch,
            raw_data=[None, None, None, None],
            effects={"Sens": (0.75, 0.60, 0.85), "Spec": (0.80, 0.70, 0.90)},
        )
        warnings = []
        monkeypatch.setattr(
            diagnostic_data_dialog.calc_fncs.QMessageBox,
            "warning",
            lambda _parent, _title, message: warnings.append(message),
        )
        try:
            dialog.show()
            dialog.resize(dialog.width(), 280)
            app.processEvents()
            field = getattr(dialog, field_name)
            field.setText(invalid_value)
            field.editingFinished.emit()
            app.processEvents()
    
            assert warnings
            assert guidance in dialog.inconsistencyLabel.text()
            assert dialog.inconsistencyLabel.wordWrap()
>           assert field.text() == restored
E           AssertionError: assert 'not numeric' == '0.75'
E             
E             - 0.75
E             + not numeric

tests/python/gui/test_diagnostic_transactional_layout.py:539: AssertionError
----------------------------- Captured stderr call -----------------------------
This plugin does not support propagateSizeHints()
_ test_direct_effect_validation_is_complete_and_reachable_with_large_font[interval] _

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7d299c0aabd0>
field_name = 'lower_text_box', invalid_value = '0.95'
guidance = 'lower CI must be less', restored = '0.6'

    @pytest.mark.parametrize(
        ("field_name", "invalid_value", "guidance", "restored"),
        [
            ("effect_text_box", "not numeric", "must be numeric", "0.75"),
            ("lower_text_box", "0.95", "lower CI must be less", "0.6"),
        ],
        ids=["effect", "interval"],
    )
    def test_direct_effect_validation_is_complete_and_reachable_with_large_font(
        monkeypatch, field_name, invalid_value, guidance, restored
    ):
        from rc_metastudio import diagnostic_data_dialog
    
        app = cast(
            QtWidgets.QApplication,
            required(
                QtWidgets.QApplication.instance() or QtWidgets.QApplication([]),
                "application",
            ),
        )
        old_font = app.font()
        enlarged = QtGui.QFont(old_font)
        enlarged.setPointSize(max(16, old_font.pointSize() + 6))
        app.setFont(enlarged)
        app, dialog = _open_data_dialog(
            monkeypatch,
            raw_data=[None, None, None, None],
            effects={"Sens": (0.75, 0.60, 0.85), "Spec": (0.80, 0.70, 0.90)},
        )
        warnings = []
        monkeypatch.setattr(
            diagnostic_data_dialog.calc_fncs.QMessageBox,
            "warning",
            lambda _parent, _title, message: warnings.append(message),
        )
        try:
            dialog.show()
            dialog.resize(dialog.width(), 280)
            app.processEvents()
            field = getattr(dialog, field_name)
            field.setText(invalid_value)
            field.editingFinished.emit()
            app.processEvents()
    
            assert warnings
            assert guidance in dialog.inconsistencyLabel.text()
            assert dialog.inconsistencyLabel.wordWrap()
>           assert field.text() == restored
E           AssertionError: assert '0.95' == '0.6'
E             
E             - 0.6
E             + 0.95

tests/python/gui/test_diagnostic_transactional_layout.py:539: AssertionError
----------------------------- Captured stderr call -----------------------------
This plugin does not support propagateSizeHints()
=========================== short test summary info ============================
FAILED tests/python/fast/test_dataset_contracts.py::test_rename_group_preserves_effects_when_the_name_contains_a_hyphen
FAILED tests/python/fast/test_dataset_ordering.py::test_dataset_group_and_follow_up_order_is_stable_across_hash_seeds
FAILED tests/python/fast/test_domain_identity.py::test_editable_labels_do_not_change_domain_identities
FAILED tests/python/gui/test_diagnostic_transactional_layout.py::test_large_font_count_overflow_and_focus_stay_inside_content
FAILED tests/python/gui/test_diagnostic_transactional_layout.py::test_direct_effect_validation_is_complete_and_reachable_with_large_font[effect]
FAILED tests/python/gui/test_diagnostic_transactional_layout.py::test_direct_effect_validation_is_complete_and_reachable_with_large_font[interval]
6 failed, 380 passed, 6 skipped in 93.04s (0:01:33)

```

## strict-types

Command: `uv run ty check --extra-search-path build/qt6-verification/generated/rc_metastudio --extra-search-path build/qt6-verification/generated/rc_metastudio/forms --extra-search-path . --extra-search-path src/rc_metastudio --extra-search-path src --extra-search-path scripts --extra-search-path tests/python/gui src/rc_metastudio scripts tests r/RCMetaR/inst/qa`

```text
["uv", "run", "ty", "check", "--extra-search-path", "build/qt6-verification/generated/rc_metastudio", "--extra-search-path", "build/qt6-verification/generated/rc_metastudio/forms", "--extra-search-path", ".", "--extra-search-path", "src/rc_metastudio", "--extra-search-path", "src", "--extra-search-path", "scripts", "--extra-search-path", "tests/python/gui", "src/rc_metastudio", "scripts", "tests", "r/RCMetaR/inst/qa"]
error[unresolved-import]: Cannot resolve imported module `pefile`
   --> scripts/inspect_windows_deployment.py:173:12
    |
172 | def _pe_imports(path: Path) -> list[dict[str, str]]:
173 |     import pefile
    |            ^^^^^^
174 |
175 |     try:
    |
info: Searched in the following paths during module resolution:
info:   1. /home/ali/Documents/Code/rc-metastudio/build/qt6-verification/generated/rc_metastudio (extra search path specified on the CLI or in your config file)
info:   2. /home/ali/Documents/Code/rc-metastudio/build/qt6-verification/generated/rc_metastudio/forms (extra search path specified on the CLI or in your config file)
info:   3. /home/ali/Documents/Code/rc-metastudio (extra search path specified on the CLI or in your config file)
info:   4. /home/ali/Documents/Code/rc-metastudio/src/rc_metastudio (extra search path specified on the CLI or in your config file)
info:   5. /home/ali/Documents/Code/rc-metastudio/src (extra search path specified on the CLI or in your config file)
info:   ... and 6 more paths. Run with `-v` to see all paths.
info: make sure your Python environment is properly configured: https://docs.astral.sh/ty/modules/#python-environment
info: rule `unresolved-import` was selected in the configuration file

error[unresolved-attribute]: Object of type `ResultsWindow` has no attribute `references_text`
   --> scripts/native_results_smoke.py:599:31
    |
597 |             "qpa": app.platformName(),
598 |             "result_text": {
599 |                 "references": results.references_text,
    |                               ^^^^^^^^^^^^^^^^^^^^^^^
600 |                 "summary": results.texts.get("Summary"),
601 |             },
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-import]: Cannot resolve imported module `pefile`
   --> scripts/r_integration_kit.py:863:12
    |
862 | def _windows_native_record(path: Path, relative: str) -> dict[str, object]:
863 |     import pefile
    |            ^^^^^^
864 |
865 |     try:
    |
info: Searched in the following paths during module resolution:
info:   1. /home/ali/Documents/Code/rc-metastudio/build/qt6-verification/generated/rc_metastudio (extra search path specified on the CLI or in your config file)
info:   2. /home/ali/Documents/Code/rc-metastudio/build/qt6-verification/generated/rc_metastudio/forms (extra search path specified on the CLI or in your config file)
info:   3. /home/ali/Documents/Code/rc-metastudio (extra search path specified on the CLI or in your config file)
info:   4. /home/ali/Documents/Code/rc-metastudio/src/rc_metastudio (extra search path specified on the CLI or in your config file)
info:   5. /home/ali/Documents/Code/rc-metastudio/src (extra search path specified on the CLI or in your config file)
info:   ... and 6 more paths. Run with `-v` to see all paths.
info: make sure your Python environment is properly configured: https://docs.astral.sh/ty/modules/#python-environment
info: rule `unresolved-import` was selected in the configuration file

error[unresolved-attribute]: Module `winreg` has no member `HKEY_CURRENT_USER`
  --> scripts/r_verification_support.py:66:14
   |
65 |     homes: list[Path] = []
66 |     roots = (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE)
   |              ^^^^^^^^^^^^^^^^^^^^^^^^
67 |     keys = (
68 |         r"Software\R-core\R",
   |
info: The member may be available on other Python versions or platforms
info: Python 3.11 was assumed when resolving the `HKEY_CURRENT_USER` attribute
  --> pyproject.toml:74:18
   |
73 | [tool.ty.environment]
74 | python-version = "3.11"
   |                  ^^^^^^ Python version configuration
75 | root = ["./src", ".", "./.agents/skills/verify-rcms/scripts"]
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Module `winreg` has no member `HKEY_LOCAL_MACHINE`
  --> scripts/r_verification_support.py:66:40
   |
65 |     homes: list[Path] = []
66 |     roots = (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE)
   |                                        ^^^^^^^^^^^^^^^^^^^^^^^^^
67 |     keys = (
68 |         r"Software\R-core\R",
   |
info: The member may be available on other Python versions or platforms
info: Python 3.11 was assumed when resolving the `HKEY_LOCAL_MACHINE` attribute
  --> pyproject.toml:74:18
   |
73 | [tool.ty.environment]
74 | python-version = "3.11"
   |                  ^^^^^^ Python version configuration
75 | root = ["./src", ".", "./.agents/skills/verify-rcms/scripts"]
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Module `winreg` has no member `OpenKey`
  --> scripts/r_verification_support.py:74:22
   |
72 |         for key_name in keys:
73 |             try:
74 |                 with winreg.OpenKey(root, key_name) as key:
   |                      ^^^^^^^^^^^^^^
75 |                     try:
76 |                         install_path, _ = winreg.QueryValueEx(key, "InstallPath")
   |
info: The member may be available on other Python versions or platforms
info: Python 3.11 was assumed when resolving the `OpenKey` attribute
  --> pyproject.toml:74:18
   |
73 | [tool.ty.environment]
74 | python-version = "3.11"
   |                  ^^^^^^ Python version configuration
75 | root = ["./src", ".", "./.agents/skills/verify-rcms/scripts"]
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Module `winreg` has no member `QueryValueEx`
  --> scripts/r_verification_support.py:76:43
   |
74 |                 with winreg.OpenKey(root, key_name) as key:
75 |                     try:
76 |                         install_path, _ = winreg.QueryValueEx(key, "InstallPath")
   |                                           ^^^^^^^^^^^^^^^^^^^
77 |                     except OSError:
78 |                         install_path = None
   |
info: The member may be available on other Python versions or platforms
info: Python 3.11 was assumed when resolving the `QueryValueEx` attribute
  --> pyproject.toml:74:18
   |
73 | [tool.ty.environment]
74 | python-version = "3.11"
   |                  ^^^^^^ Python version configuration
75 | root = ["./src", ".", "./.agents/skills/verify-rcms/scripts"]
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Module `winreg` has no member `QueryValueEx`
  --> scripts/r_verification_support.py:82:46
   |
80 |                         homes.append(Path(install_path))
81 |                     try:
82 |                         current_version, _ = winreg.QueryValueEx(key, "Current Version")
   |                                              ^^^^^^^^^^^^^^^^^^^
83 |                     except OSError:
84 |                         current_version = None
   |
info: The member may be available on other Python versions or platforms
info: Python 3.11 was assumed when resolving the `QueryValueEx` attribute
  --> pyproject.toml:74:18
   |
73 | [tool.ty.environment]
74 | python-version = "3.11"
   |                  ^^^^^^ Python version configuration
75 | root = ["./src", ".", "./.agents/skills/verify-rcms/scripts"]
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Module `winreg` has no member `OpenKey`
  --> scripts/r_verification_support.py:87:34
   |
85 |                     if current_version:
86 |                         try:
87 |                             with winreg.OpenKey(key, current_version) as version_key:
   |                                  ^^^^^^^^^^^^^^
88 |                                 version_install_path, _ = winreg.QueryValueEx(
89 |                                     version_key, "InstallPath"
   |
info: The member may be available on other Python versions or platforms
info: Python 3.11 was assumed when resolving the `OpenKey` attribute
  --> pyproject.toml:74:18
   |
73 | [tool.ty.environment]
74 | python-version = "3.11"
   |                  ^^^^^^ Python version configuration
75 | root = ["./src", ".", "./.agents/skills/verify-rcms/scripts"]
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Module `winreg` has no member `QueryValueEx`
  --> scripts/r_verification_support.py:88:59
   |
86 |                         try:
87 |                             with winreg.OpenKey(key, current_version) as version_key:
88 |                                 version_install_path, _ = winreg.QueryValueEx(
   |                                                           ^^^^^^^^^^^^^^^^^^^
89 |                                     version_key, "InstallPath"
90 |                                 )
   |
info: The member may be available on other Python versions or platforms
info: Python 3.11 was assumed when resolving the `QueryValueEx` attribute
  --> pyproject.toml:74:18
   |
73 | [tool.ty.environment]
74 | python-version = "3.11"
   |                  ^^^^^^ Python version configuration
75 | root = ["./src", ".", "./.agents/skills/verify-rcms/scripts"]
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Module `winreg` has no member `EnumKey`
   --> scripts/r_verification_support.py:98:39
    |
 96 |                     while True:
 97 |                         try:
 98 |                             version = winreg.EnumKey(key, index)
    |                                       ^^^^^^^^^^^^^^
 99 |                         except OSError:
100 |                             break
    |
info: The member may be available on other Python versions or platforms
info: Python 3.11 was assumed when resolving the `EnumKey` attribute
  --> pyproject.toml:74:18
   |
73 | [tool.ty.environment]
74 | python-version = "3.11"
   |                  ^^^^^^ Python version configuration
75 | root = ["./src", ".", "./.agents/skills/verify-rcms/scripts"]
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Module `winreg` has no member `OpenKey`
   --> scripts/r_verification_support.py:103:34
    |
101 |                         index += 1
102 |                         try:
103 |                             with winreg.OpenKey(key, version) as version_key:
    |                                  ^^^^^^^^^^^^^^
104 |                                 version_install_path, _ = winreg.QueryValueEx(
105 |                                     version_key, "InstallPath"
    |
info: The member may be available on other Python versions or platforms
info: Python 3.11 was assumed when resolving the `OpenKey` attribute
  --> pyproject.toml:74:18
   |
73 | [tool.ty.environment]
74 | python-version = "3.11"
   |                  ^^^^^^ Python version configuration
75 | root = ["./src", ".", "./.agents/skills/verify-rcms/scripts"]
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Module `winreg` has no member `QueryValueEx`
   --> scripts/r_verification_support.py:104:59
    |
102 |                         try:
103 |                             with winreg.OpenKey(key, version) as version_key:
104 |                                 version_install_path, _ = winreg.QueryValueEx(
    |                                                           ^^^^^^^^^^^^^^^^^^^
105 |                                     version_key, "InstallPath"
106 |                                 )
    |
info: The member may be available on other Python versions or platforms
info: Python 3.11 was assumed when resolving the `QueryValueEx` attribute
  --> pyproject.toml:74:18
   |
73 | [tool.ty.environment]
74 | python-version = "3.11"
   |                  ^^^^^^ Python version configuration
75 | root = ["./src", ".", "./.agents/skills/verify-rcms/scripts"]
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Attribute `setData` is not defined on `None` in union `Unknown | QTableWidgetItem | None`
   --> src/rc_metastudio/continuous_data_dialog.py:808:17
    |
806 |                 return
807 |             with QSignalBlocker(self.simple_table):
808 |                 self.simple_table.item(row, col).setData(Qt.ItemDataRole.UserRole, True)
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
809 |             self.impute_data()
810 |         except Exception as e:
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Attribute `setToolTip` is not defined on `None` in union `Unknown | QTableWidgetItem | None`
   --> src/rc_metastudio/continuous_data_dialog.py:863:13
    |
861 |                     table.item(row, col), f"continuous table cell ({row}, {col})"
862 |                 ).setText(str_val)
863 |             table.item(row, col).setToolTip(str_val)
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
864 |             if supplied is not None or not str_val:
865 |                 table.item(row, col).setData(Qt.ItemDataRole.UserRole, bool(supplied and str_val))
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Attribute `setData` is not defined on `None` in union `Unknown | QTableWidgetItem | None`
   --> src/rc_metastudio/continuous_data_dialog.py:865:17
    |
863 |             table.item(row, col).setToolTip(str_val)
864 |             if supplied is not None or not str_val:
865 |                 table.item(row, col).setData(Qt.ItemDataRole.UserRole, bool(supplied and str_val))
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
866 |
867 |     def _disable_row_if_filled(self, table, row, col):
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Attribute `text` is not defined on `None` in union `Unknown | QTableWidgetItem | None`
   --> src/rc_metastudio/continuous_data_dialog.py:938:19
    |
936 |         for table in self.tables:
937 |             old_tables_data.append([
938 |                 [(table.item(row, col).text(), bool(table.item(row, col).data(Qt.ItemDataRole.UserRole)))
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^
939 |                  for col in range(table.columnCount())]
940 |                 for row in range(table.rowCount())
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Attribute `data` is not defined on `None` in union `Unknown | QTableWidgetItem | None`
   --> src/rc_metastudio/continuous_data_dialog.py:938:53
    |
936 |         for table in self.tables:
937 |             old_tables_data.append([
938 |                 [(table.item(row, col).text(), bool(table.item(row, col).data(Qt.ItemDataRole.UserRole)))
    |                                                     ^^^^^^^^^^^^^^^^^^^^^^^^^
939 |                  for col in range(table.columnCount())]
940 |                 for row in range(table.rowCount())
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Attribute `data` is not defined on `None` in union `Unknown | QTableWidgetItem | None`
   --> src/rc_metastudio/continuous_data_dialog.py:977:46
    |
975 |             for var_index, var_name in enumerate(var_names):
976 |                 var_value = self._get_float(row_index, var_index)
977 |                 if var_value is not None and self.simple_table.item(row_index, var_index).data(Qt.ItemDataRole.UserRole):
    |                                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
978 |                     current_values[self._imputation_field_name(var_name)] = var_value
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[index-out-of-bounds]: Index 1 is out of bounds for tuple `tuple[str]` with length 1
  --> tests/e2e/arm_names.py:74:66
   |
72 |                     assert table.horizontalHeaderItem(1).text() == "No event"
73 |                 if len(entered)==2:
74 |                     assert table.verticalHeaderItem(1).text() == expected[1]
   |                                                                  ^^^^^^^^
75 |                 record("round5-arm-calculator", dialog, case=case, groups=expected, capture_surface="desktop-composite")
76 |                 dialog.reject()
   |
info: rule `index-out-of-bounds` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `template_btn`
  --> tests/e2e/arm_names.py:90:28
   |
88 |             template = work / f"arms-{case}-template.csv"
89 |             with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(template), "CSV")):
90 |                 click(app, page.template_btn)
   |                            ^^^^^^^^^^^^^^^^^
91 |             with template.open(encoding="utf-8-sig") as stream:
92 |                 canonical = next(csv.reader(stream))
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `select_file_btn`
   --> tests/e2e/arm_names.py:107:32
    |
105 |                     writer.writerow(values)
106 |                 with patch.object(QtWidgets.QFileDialog, "getOpenFileName", return_value=(str(source), "CSV")):
107 |                     click(app, page.select_file_btn)
    |                                ^^^^^^^^^^^^^^^^^^^^
108 |                 assert page.isComplete(), page.import_status.text()
109 |                 displayed=[page.preview_table.horizontalHeaderItem(i).text() for i in range(page.preview_table.columnCount())]
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Attribute `isComplete` is not defined on `None` in union `QWizardPage | None`
   --> tests/e2e/arm_names.py:108:24
    |
106 |                 with patch.object(QtWidgets.QFileDialog, "getOpenFileName", return_value=(str(source), "CSV")):
107 |                     click(app, page.select_file_btn)
108 |                 assert page.isComplete(), page.import_status.text()
    |                        ^^^^^^^^^^^^^^^
109 |                 displayed=[page.preview_table.horizontalHeaderItem(i).text() for i in range(page.preview_table.columnCount())]
110 |                 assert displayed == canonical, (displayed, canonical)
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `import_status`
   --> tests/e2e/arm_names.py:108:43
    |
106 |                 with patch.object(QtWidgets.QFileDialog, "getOpenFileName", return_value=(str(source), "CSV")):
107 |                     click(app, page.select_file_btn)
108 |                 assert page.isComplete(), page.import_status.text()
    |                                           ^^^^^^^^^^^^^^^^^^
109 |                 displayed=[page.preview_table.horizontalHeaderItem(i).text() for i in range(page.preview_table.columnCount())]
110 |                 assert displayed == canonical, (displayed, canonical)
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `preview_table`
   --> tests/e2e/arm_names.py:109:28
    |
107 |                     click(app, page.select_file_btn)
108 |                 assert page.isComplete(), page.import_status.text()
109 |                 displayed=[page.preview_table.horizontalHeaderItem(i).text() for i in range(page.preview_table.columnCount())]
    |                            ^^^^^^^^^^^^^^^^^^
110 |                 assert displayed == canonical, (displayed, canonical)
111 |                 if data_type == "binary":
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `preview_table`
   --> tests/e2e/arm_names.py:109:93
    |
107 |                     click(app, page.select_file_btn)
108 |                 assert page.isComplete(), page.import_status.text()
109 |                 displayed=[page.preview_table.horizontalHeaderItem(i).text() for i in range(page.preview_table.columnCount())]
    |                                                                                             ^^^^^^^^^^^^^^^^^^
110 |                 assert displayed == canonical, (displayed, canonical)
111 |                 if data_type == "binary":
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `preview_table`
   --> tests/e2e/arm_names.py:112:29
    |
110 | …     assert displayed == canonical, (displayed, canonical)
111 | …     if data_type == "binary":
112 | …         assert [page.preview_table.item(0, i).text() for i in range(2, 6)] == ["4", "20", "6", "22"]
    |                   ^^^^^^^^^^^^^^^^^^
113 | …     record("round5-arm-csv-preview", wizard, case=case, spelling=spelling, headers=displayed, exports={"template":str(template),"in…
114 | …     page.import_tabs.setCurrentWidget(page.mapping_table)
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `import_tabs`
   --> tests/e2e/arm_names.py:114:17
    |
112 | …         assert [page.preview_table.item(0, i).text() for i in range(2, 6)] == ["4", "20", "6", "22"]
113 | …     record("round5-arm-csv-preview", wizard, case=case, spelling=spelling, headers=displayed, exports={"template":str(template),"in…
114 | …     page.import_tabs.setCurrentWidget(page.mapping_table)
    |       ^^^^^^^^^^^^^^^^
115 | …     assert not any("tx " in control.itemText(i).casefold() for control in page.mapping_controls for i in range(control.count()))
116 | …     record("round5-arm-csv-mapping", wizard, case=case, spelling=spelling)
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `mapping_table`
   --> tests/e2e/arm_names.py:114:51
    |
112 | …         assert [page.preview_table.item(0, i).text() for i in range(2, 6)] == ["4", "20", "6", "22"]
113 | …     record("round5-arm-csv-preview", wizard, case=case, spelling=spelling, headers=displayed, exports={"template":str(template),"in…
114 | …     page.import_tabs.setCurrentWidget(page.mapping_table)
    |                                         ^^^^^^^^^^^^^^^^^^
115 | …     assert not any("tx " in control.itemText(i).casefold() for control in page.mapping_controls for i in range(control.count()))
116 | …     record("round5-arm-csv-mapping", wizard, case=case, spelling=spelling)
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `mapping_controls`
   --> tests/e2e/arm_names.py:115:87
    |
113 | …         record("round5-arm-csv-preview", wizard, case=case, spelling=spelling, headers=displayed, exports={"template":str(template)…
114 | …         page.import_tabs.setCurrentWidget(page.mapping_table)
115 | …         assert not any("tx " in control.itemText(i).casefold() for control in page.mapping_controls for i in range(control.count()))
    |                                                                                 ^^^^^^^^^^^^^^^^^^^^^
116 | …         record("round5-arm-csv-mapping", wizard, case=case, spelling=spelling)
117 | …     wizard.reject()
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
  --> tests/e2e/audit_round3.py:18:18
   |
16 |     assert expected in " ".join(text.split()), (expected, text)
17 |     caption = nodes[-1]
18 |     size = float(re.search(r"font-size:\s*([\d.]+)px", caption.attrib["style"])[1])
   |                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 |     assert size >= 12.9, ("unreadable caption", caption.attrib)
   |
info: rule `not-subscriptable` was selected in the configuration file

error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
   --> tests/e2e/audit_round3.py:115:28
    |
113 |             x, y = float(node.attrib["x"]), float(node.attrib["y"])
114 |             width = float(node.attrib["textLength"].removesuffix("px"))
115 |             height = float(re.search(r"font-size: ([\d.]+)px", node.attrib["style"])[1])
    |                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
116 |             anchor = node.attrib.get("text-anchor", "start")
117 |             left = x-width if anchor == "end" else x-width/2 if anchor == "middle" else x
    |
info: rule `not-subscriptable` was selected in the configuration file

error[possibly-unresolved-reference]: Name `lines` used when possibly not defined
   --> tests/e2e/audit_round3.py:254:25
    |
252 | …     if workflow in {"cumulative", "leave-one-out"}:
253 | …         row_y = [y for text, y in nodes if text in data["slab"]]
254 | …         for line in lines if data["measure"] in {"OR", "RR", "HR", "IRR", "MD", "SMD"} and data["range"][0] <= 0 <= data["range"][1…
    |                       ^^^^^
255 | …             if (abs(float(line["x1"]) - float(line["x2"])) < .01
256 | …                 and abs(float(line["y1"]) - float(line["y2"])) > 50
    |
info: rule `possibly-unresolved-reference` was selected in the configuration file

error[possibly-unresolved-reference]: Name `ticks` used when possibly not defined
   --> tests/e2e/audit_round3.py:257:77
    |
255 |                 if (abs(float(line["x1"]) - float(line["x2"])) < .01
256 |                     and abs(float(line["y1"]) - float(line["y2"])) > 50
257 |                     and any(abs(float(line["x1"]) - tick) < .02 for tick in ticks)):
    |                                                                             ^^^^^
258 |                     assert max(float(line["y1"]), float(line["y2"])) <= max(row_y) + 15, ("null reaches footer", line, row_y)
259 |         view.report_action.setChecked(False)
    |
info: rule `possibly-unresolved-reference` was selected in the configuration file

error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
   --> tests/e2e/audit_round3.py:455:51
    |
453 | …     title = next(node for node in svg.iter("{http://www.w3.org/2000/svg}text")
454 | …                  if "Entered effect" in "".join(node.itertext()))
455 | …     title_x = float(title.attrib.get("x", re.search(r"translate\(([-\d.]+)", title.attrib.get("transform", "translate(0"))[1]))
    |                                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
456 | …     title_right = title_x + float(re.search(r"font-size:\s*([\d.]+)px", title.attrib["style"])[1])
457 | …     tick_left = min(float(node.attrib["x"]) - float(node.attrib["textLength"].removesuffix("px")) for node in tick_nodes)
    |
info: rule `not-subscriptable` was selected in the configuration file

error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
   --> tests/e2e/audit_round3.py:456:43
    |
454 | …                  if "Entered effect" in "".join(node.itertext()))
455 | …     title_x = float(title.attrib.get("x", re.search(r"translate\(([-\d.]+)", title.attrib.get("transform", "translate(0"))[1]))
456 | …     title_right = title_x + float(re.search(r"font-size:\s*([\d.]+)px", title.attrib["style"])[1])
    |                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
457 | …     tick_left = min(float(node.attrib["x"]) - float(node.attrib["textLength"].removesuffix("px")) for node in tick_nodes)
458 | …     assert tick_left - title_right >= 4, ("tick/title gap", tick_left, title.attrib)
    |
info: rule `not-subscriptable` was selected in the configuration file

error[unresolved-attribute]: Attribute `text` is not defined on `None` in union `Unknown | QTableWidgetItem | None`
   --> tests/e2e/audit_round3.py:627:24
    |
625 |                 click(app, page.select_file_btn)
626 |             assert page.isComplete(), page.import_status.text()
627 |             headers = [page.preview_table.horizontalHeaderItem(i).text() for i in range(page.preview_table.columnCount())]
    |                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
628 |             assert "Estimate" in headers and "TX Mean" not in headers, headers
629 |             record("round4-contextual-csv", wizard, headers=headers, input_headers=page.required_header_labels,
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[invalid-argument-type]: Argument to bound method `__init__` is incorrect
   --> tests/e2e/audit_round3.py:713:31
    |
711 |             for title, path in view.results.display_images.items():
712 |                 r_bridge.load_in_r(str(view.params_paths[title]) + ".plotdata")
713 |                 bounds = list(r_bridge.ro.r('RCMetaR:::rcmetar.forest.layout.preflight(plot.data)$x$alim'))
    |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ Expected `Iterable[Unknown]`, found `object`
714 |                 assert all(math.isfinite(x) for x in bounds) and bounds[1] > bounds[0], bounds
715 |                 nodes = list(ET.parse(path).iter("{http://www.w3.org/2000/svg}text"))
    |
info: Matching overload defined here
    --> stdlib/builtins.pyi:2839:9
     |
2837 |     def __init__(self) -> None: ...
2838 |     @overload
2839 |     def __init__(self, iterable: Iterable[_T], /) -> None: ...
     |         ^^^^^^^^       ---------------------- Parameter declared here
2840 |     def copy(self) -> list[_T]:
2841 |         """Return a shallow copy of the list."""
     |
info: Non-matching overloads for bound method `__init__`:
info:   (self) -> None
info: rule `invalid-argument-type` was selected in the configuration file

error[possibly-unresolved-reference]: Name `bounds` used when possibly not defined
   --> tests/e2e/audit_round3.py:723:92
    |
721 |                 assert len(ticks) >= 2, ticks
722 |                 assert len(labels) == len(ticks), ("duplicate collapsed-axis labels", style, labels)
723 |             record("round3-degenerate-axis", view, style=style, entered=[1, 1e-20], bounds=bounds,
    |                                                                                            ^^^^^^
724 |                    ticks=sorted(ticks), plots=dict(view.results.display_images))
725 |             if style == "default":
    |
info: rule `possibly-unresolved-reference` was selected in the configuration file

error[possibly-unresolved-reference]: Name `ticks` used when possibly not defined
   --> tests/e2e/audit_round3.py:724:33
    |
722 |                 assert len(labels) == len(ticks), ("duplicate collapsed-axis labels", style, labels)
723 |             record("round3-degenerate-axis", view, style=style, entered=[1, 1e-20], bounds=bounds,
724 |                    ticks=sorted(ticks), plots=dict(view.results.display_images))
    |                                 ^^^^^
725 |             if style == "default":
726 |                 view.graphics_view.verticalScrollBar().setValue(view.graphics_view.verticalScrollBar().maximum())
    |
info: rule `possibly-unresolved-reference` was selected in the configuration file

error[possibly-unresolved-reference]: Name `bounds` used when possibly not defined
   --> tests/e2e/audit_round3.py:727:83
    |
725 |             if style == "default":
726 |                 view.graphics_view.verticalScrollBar().setValue(view.graphics_view.verticalScrollBar().maximum())
727 |                 record("round3-degenerate-axis-bottom", view, style=style, bounds=bounds)
    |                                                                                   ^^^^^^
728 |             view.close()
729 |             window.workspace.mark_saved()
    |
info: rule `possibly-unresolved-reference` was selected in the configuration file

error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
   --> tests/e2e/audit_round3.py:924:36
    |
922 | …         continue
923 | …     y = float(node.attrib["y"])
924 | …     height = float(re.search(r"font-size:\s*([\d.]+)px", node.attrib["style"])[1])
    |                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
925 | …     for rule in ET.parse(path).iter("{http://www.w3.org/2000/svg}line"):
926 | …         if abs(float(rule.attrib["x2"]) - float(rule.attrib["x1"])) < 500 or abs(float(rule.attrib["y2"]) - float(rule.attrib["y1"]…
    |
info: rule `not-subscriptable` was selected in the configuration file

error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
    --> tests/e2e/audit_round3.py:1062:28
     |
1060 |             x, y = float(node.attrib["x"]), float(node.attrib["y"])
1061 |             width = float(node.attrib["textLength"].removesuffix("px"))
1062 |             height = float(re.search(r"font-size:\s*([\d.]+)px", node.attrib["style"])[1]) * .8
     |                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1063 |             anchor = node.attrib.get("text-anchor", "start")
1064 |             left = x - (width if anchor == "end" else width/2 if anchor == "middle" else 0)
     |
info: rule `not-subscriptable` was selected in the configuration file

error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
    --> tests/e2e/audit_round3.py:1079:28
     |
1077 |                 continue
1078 |             x, y = float(node.attrib["x"]), float(node.attrib["y"])
1079 |             height = float(re.search(r"font-size:\s*([\d.]+)px", node.attrib["style"])[1])
     |                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1080 |             for line in svg.iter("{http://www.w3.org/2000/svg}line"):
1081 |                 if abs(float(line.attrib["y1"]) - float(line.attrib["y2"])) < .01:
     |
info: rule `not-subscriptable` was selected in the configuration file

error[no-matching-overload]: No overload of function `keyClick` matches arguments
  --> tests/e2e/precision_inputs.py:29:13
   |
27 |         before = editor.text()
28 |         if text is not None:
29 |             QTest.keyClick(editor, QtCore.Qt.Key.Key_A, QtCore.Qt.KeyboardModifier.ControlModifier)
   |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
30 |             QTest.keyClicks(editor, text)
31 |         QTest.keyClick(editor, QtCore.Qt.Key.Key_Return)
   |
info: First overload defined here
   --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:149:9
    |
147 | … def keyClicks(self, widget: QtWidgets.QWidget|None, sequence: str|None, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
148 | … @typing.overload
149 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: QtCore.Qt.Key, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
150 | … @typing.overload
151 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: str, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |
info: Possible overloads for function `keyClick`:
info:   (self, widget: QWidget | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, widget: QWidget | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info: rule `no-matching-overload` was selected in the configuration file

error[missing-argument]: No argument provided for required parameter `sequence` of function `keyClicks`
  --> tests/e2e/precision_inputs.py:30:13
   |
28 |         if text is not None:
29 |             QTest.keyClick(editor, QtCore.Qt.Key.Key_A, QtCore.Qt.KeyboardModifier.ControlModifier)
30 |             QTest.keyClicks(editor, text)
   |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
31 |         QTest.keyClick(editor, QtCore.Qt.Key.Key_Return)
32 |         app.processEvents()
   |
info: Parameter declared here
   --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:147:57
    |
145 |     @typing.overload
146 |     def keyEvent(self, action: 'QTest.KeyAction', window: QtGui.QWindow|None, ascii: str, modifier: QtCore.Qt.KeyboardModifier = ...,…
147 |     def keyClicks(self, widget: QtWidgets.QWidget|None, sequence: str|None, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = …
    |                                                         ^^^^^^^^^^^^^^^^^^
148 |     @typing.overload
149 |     def keyClick(self, widget: QtWidgets.QWidget|None, key: QtCore.Qt.Key, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = .…
    |
info: rule `missing-argument` was selected in the configuration file

error[no-matching-overload]: No overload of function `keyClick` matches arguments
  --> tests/e2e/precision_inputs.py:31:9
   |
29 |             QTest.keyClick(editor, QtCore.Qt.Key.Key_A, QtCore.Qt.KeyboardModifier.ControlModifier)
30 |             QTest.keyClicks(editor, text)
31 |         QTest.keyClick(editor, QtCore.Qt.Key.Key_Return)
   |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
32 |         app.processEvents()
33 |         return before
   |
info: First overload defined here
   --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:149:9
    |
147 | … def keyClicks(self, widget: QtWidgets.QWidget|None, sequence: str|None, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
148 | … @typing.overload
149 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: QtCore.Qt.Key, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
150 | … @typing.overload
151 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: str, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |
info: Possible overloads for function `keyClick`:
info:   (self, widget: QWidget | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, widget: QWidget | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info: rule `no-matching-overload` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `outcome_name_LineEdit`
  --> tests/e2e/precision_inputs.py:70:5
   |
68 |     wizard = main_wizard.MainWizard(path='csv_import')
69 |     wizard.set_dataset_info(dict(arms='two', data_type='continuous', sub_type='means', effect='SMD', metric_choices=[], name='Precisio…
70 |     wizard.page(main_wizard.Page_OutcomeName).outcome_name_LineEdit.setText('Precision')
   |     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
71 |     wizard.setStartId(main_wizard.Page_CsvImport)
72 |     wizard.restart()
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[no-matching-overload]: No overload of function `mouseClick` matches arguments
  --> tests/e2e/precision_inputs.py:77:9
   |
75 |     page = wizard.currentPage()
76 |     with patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(str(csv), '')):
77 |         QTest.mouseClick(page.select_file_btn, QtCore.Qt.MouseButton.LeftButton)
   |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
78 |     assert page.isComplete(), page.required_header_labels
79 |     record('csv-precision-preview', wizard, inputs=expected)
   |
info: First overload defined here
   --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:111:9
    |
109 | … def mouseDClick(self, window: QtGui.QWindow|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., pos: QtCore.QPoint = ..., delay: int = ...) -> None: ...
110 | … @typing.overload
111 | … def mouseClick(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., pos: QtCore.QPoint = ..., delay: int = ...) -> None: ...
    |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
112 | … @typing.overload
113 | … def mouseClick(self, window: QtGui.QWindow|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., pos: QtCore.QPoint = ..., delay: int = ...) -> None: ...
    |
info: Possible overloads for function `mouseClick`:
info:   (self, widget: QWidget | None, button: MouseButton, modifier: KeyboardModifier = ..., pos: QPoint = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, button: MouseButton, modifier: KeyboardModifier = ..., pos: QPoint = ..., delay: int = ...) -> None
info: rule `no-matching-overload` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `select_file_btn`
  --> tests/e2e/precision_inputs.py:77:26
   |
75 |     page = wizard.currentPage()
76 |     with patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(str(csv), '')):
77 |         QTest.mouseClick(page.select_file_btn, QtCore.Qt.MouseButton.LeftButton)
   |                          ^^^^^^^^^^^^^^^^^^^^
78 |     assert page.isComplete(), page.required_header_labels
79 |     record('csv-precision-preview', wizard, inputs=expected)
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Attribute `isComplete` is not defined on `None` in union `QWizardPage | None`
  --> tests/e2e/precision_inputs.py:78:12
   |
76 |     with patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(str(csv), '')):
77 |         QTest.mouseClick(page.select_file_btn, QtCore.Qt.MouseButton.LeftButton)
78 |     assert page.isComplete(), page.required_header_labels
   |            ^^^^^^^^^^^^^^^
79 |     record('csv-precision-preview', wizard, inputs=expected)
80 |     window._handle_wizard_results(wizard.get_results())
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `required_header_labels`
  --> tests/e2e/precision_inputs.py:78:31
   |
76 |     with patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(str(csv), '')):
77 |         QTest.mouseClick(page.select_file_btn, QtCore.Qt.MouseButton.LeftButton)
78 |     assert page.isComplete(), page.required_header_labels
   |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
79 |     record('csv-precision-preview', wizard, inputs=expected)
80 |     window._handle_wizard_results(wizard.get_results())
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
  --> tests/e2e/review1_design.py:88:17
   |
86 |             assert wizard.get_wizard_path() == expected
87 |             if app.platformName() in {'windows', 'xcb', 'cocoa'}:
88 |                 QTest.qWait(250)
   |                 ^^^^^^^^^^^^^^^^
89 |             record('review1-start-wizard-' + expected, wizard)
90 |             wizard.reject()
   |
info: Parameter declared here
  --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:93:21
   |
91 |     @typing.overload
92 |     def qWaitForWindowActive(self, widget: QtWidgets.QWidget|None, timeout: int = ...) -> bool: ...
93 |     def qWait(self, ms: int) -> None: ...
   |                     ^^^^^^^
94 |     @typing.overload
95 |     def mouseRelease(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., …
   |
info: rule `missing-argument` was selected in the configuration file

error[invalid-argument-type]: Argument to function `qWait` is incorrect
  --> tests/e2e/review1_design.py:88:29
   |
86 |             assert wizard.get_wizard_path() == expected
87 |             if app.platformName() in {'windows', 'xcb', 'cocoa'}:
88 |                 QTest.qWait(250)
   |                             ^^^ Expected `QTest`, found `Literal[250]`
89 |             record('review1-start-wizard-' + expected, wizard)
90 |             wizard.reject()
   |
info: Function defined here
  --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:93:9
   |
91 |     @typing.overload
92 |     def qWaitForWindowActive(self, widget: QtWidgets.QWidget|None, timeout: int = ...) -> bool: ...
93 |     def qWait(self, ms: int) -> None: ...
   |         ^^^^^ ---- Parameter declared here
94 |     @typing.overload
95 |     def mouseRelease(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., …
   |
info: rule `invalid-argument-type` was selected in the configuration file

error[no-matching-overload]: No overload of function `keyClick` matches arguments
   --> tests/e2e/review1_design.py:131:5
    |
129 |     keyboard_traversal(app, window, [window.analysis_button, window.navigation_dimension, window.tableView], record, "workspace")
130 |     window.tableView.setFocus()
131 |     QTest.keyClick(window.tableView, QtCore.Qt.Key.Key_Tab, QtCore.Qt.KeyboardModifier.ControlModifier)
    |     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
132 |     app.processEvents()
133 |     assert app.focusWidget() is not window.tableView, "Ctrl+Tab cannot leave the study grid"
    |
info: First overload defined here
   --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:149:9
    |
147 | … def keyClicks(self, widget: QtWidgets.QWidget|None, sequence: str|None, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
148 | … @typing.overload
149 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: QtCore.Qt.Key, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
150 | … @typing.overload
151 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: str, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |
info: Possible overloads for function `keyClick`:
info:   (self, widget: QWidget | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, widget: QWidget | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info: rule `no-matching-overload` was selected in the configuration file

error[no-matching-overload]: No overload of function `mouseRelease` matches arguments
   --> tests/e2e/review1_design.py:149:17
    |
147 |                 prerequisite = window.action_subgroup_ma
148 |                 assert not prerequisite.isEnabled()
149 |                 QTest.mouseRelease(menu, QtCore.Qt.MouseButton.LeftButton, pos=menu.actionGeometry(prerequisite).center())
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
150 |                 QTest.mouseMove(menu, menu.actionGeometry(window.action_go).center())
151 |                 QTest.mouseMove(menu, menu.actionGeometry(prerequisite).center())
    |
info: First overload defined here
  --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:95:9
   |
93 | … def qWait(self, ms: int) -> None: ...
94 | … @typing.overload
95 | … def mouseRelease(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., pos: QtCore.QPoint = ..., delay: int = ...) -> None: ...
   |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
96 | … @typing.overload
97 | … def mouseRelease(self, window: QtGui.QWindow|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., pos: QtCore.QPoint = ..., delay: int = ...) -> None: ...
   |
info: Possible overloads for function `mouseRelease`:
info:   (self, widget: QWidget | None, button: MouseButton, modifier: KeyboardModifier = ..., pos: QPoint = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, button: MouseButton, modifier: KeyboardModifier = ..., pos: QPoint = ..., delay: int = ...) -> None
info: rule `no-matching-overload` was selected in the configuration file

error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
   --> tests/e2e/review1_design.py:152:17
    |
150 | …     QTest.mouseMove(menu, menu.actionGeometry(window.action_go).center())
151 | …     QTest.mouseMove(menu, menu.actionGeometry(prerequisite).center())
152 | …     QTest.qWait(1200)
    |       ^^^^^^^^^^^^^^^^^
153 | …     assert QtWidgets.QToolTip.isVisible() and QtWidgets.QToolTip.text() == prerequisite.toolTip(), QtWidgets.QToolTip.text()
154 | …     record('round5-analysis-prerequisite-tooltip', window, tooltip=QtWidgets.QToolTip.text(), capture_surface="desktop-composite")
    |
info: Parameter declared here
  --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:93:21
   |
91 |     @typing.overload
92 |     def qWaitForWindowActive(self, widget: QtWidgets.QWidget|None, timeout: int = ...) -> bool: ...
93 |     def qWait(self, ms: int) -> None: ...
   |                     ^^^^^^^
94 |     @typing.overload
95 |     def mouseRelease(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., …
   |
info: rule `missing-argument` was selected in the configuration file

error[invalid-argument-type]: Argument to function `qWait` is incorrect
   --> tests/e2e/review1_design.py:152:29
    |
150 | …     QTest.mouseMove(menu, menu.actionGeometry(window.action_go).center())
151 | …     QTest.mouseMove(menu, menu.actionGeometry(prerequisite).center())
152 | …     QTest.qWait(1200)
    |                   ^^^^ Expected `QTest`, found `Literal[1200]`
153 | …     assert QtWidgets.QToolTip.isVisible() and QtWidgets.QToolTip.text() == prerequisite.toolTip(), QtWidgets.QToolTip.text()
154 | …     record('round5-analysis-prerequisite-tooltip', window, tooltip=QtWidgets.QToolTip.text(), capture_surface="desktop-composite")
    |
info: Function defined here
  --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:93:9
   |
91 |     @typing.overload
92 |     def qWaitForWindowActive(self, widget: QtWidgets.QWidget|None, timeout: int = ...) -> bool: ...
93 |     def qWait(self, ms: int) -> None: ...
   |         ^^^^^ ---- Parameter declared here
94 |     @typing.overload
95 |     def mouseRelease(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., …
   |
info: rule `invalid-argument-type` was selected in the configuration file

error[no-matching-overload]: No overload of function `mouseClick` matches arguments
   --> tests/e2e/review1_design.py:157:13
    |
155 | …             QtWidgets.QToolTip.hideText()
156 | …         record('round5-analysis-menu', menu, actions=[dict(text=action.text(), enabled=action.isEnabled(), tooltip=action.toolTip()…
157 | …         QTest.mouseClick(menu, QtCore.Qt.MouseButton.LeftButton, pos=menu.actionGeometry(window.action_go).center())
    |           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
158 | …     except Exception as error:
159 | …         menu_errors.append(str(error))
    |
info: First overload defined here
   --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:111:9
    |
109 | … def mouseDClick(self, window: QtGui.QWindow|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., pos: QtCore.QPoint = ..., delay: int = ...) -> None: ...
110 | … @typing.overload
111 | … def mouseClick(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., pos: QtCore.QPoint = ..., delay: int = ...) -> None: ...
    |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
112 | … @typing.overload
113 | … def mouseClick(self, window: QtGui.QWindow|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., pos: QtCore.QPoint = ..., delay: int = ...) -> None: ...
    |
info: Possible overloads for function `mouseClick`:
info:   (self, widget: QWidget | None, button: MouseButton, modifier: KeyboardModifier = ..., pos: QPoint = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, button: MouseButton, modifier: KeyboardModifier = ..., pos: QPoint = ..., delay: int = ...) -> None
info: rule `no-matching-overload` was selected in the configuration file

error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
   --> tests/e2e/review1_design.py:223:5
    |
221 |     window.activateWindow()
222 |     controls[0].setFocus(QtCore.Qt.FocusReason.TabFocusReason)
223 |     QTest.qWait(80)
    |     ^^^^^^^^^^^^^^^
224 |     visited, reached = [], set()
225 |     for _ in range(300):
    |
info: Parameter declared here
  --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:93:21
   |
91 |     @typing.overload
92 |     def qWaitForWindowActive(self, widget: QtWidgets.QWidget|None, timeout: int = ...) -> bool: ...
93 |     def qWait(self, ms: int) -> None: ...
   |                     ^^^^^^^
94 |     @typing.overload
95 |     def mouseRelease(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., …
   |
info: rule `missing-argument` was selected in the configuration file

error[invalid-argument-type]: Argument to function `qWait` is incorrect
   --> tests/e2e/review1_design.py:223:17
    |
221 |     window.activateWindow()
222 |     controls[0].setFocus(QtCore.Qt.FocusReason.TabFocusReason)
223 |     QTest.qWait(80)
    |                 ^^ Expected `QTest`, found `Literal[80]`
224 |     visited, reached = [], set()
225 |     for _ in range(300):
    |
info: Function defined here
  --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:93:9
   |
91 |     @typing.overload
92 |     def qWaitForWindowActive(self, widget: QtWidgets.QWidget|None, timeout: int = ...) -> bool: ...
93 |     def qWait(self, ms: int) -> None: ...
   |         ^^^^^ ---- Parameter declared here
94 |     @typing.overload
95 |     def mouseRelease(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., …
   |
info: rule `invalid-argument-type` was selected in the configuration file

error[no-matching-overload]: No overload of function `keyClick` matches arguments
   --> tests/e2e/review1_design.py:235:9
    |
233 |             break
234 |         modifier = QtCore.Qt.KeyboardModifier.NoModifier
235 |         QTest.keyClick(focus, QtCore.Qt.Key.Key_Tab, modifier)
    |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
236 |         app.processEvents()
237 |     assert len(reached) == len(controls), (surface, reached, [c.objectName() for c in controls], visited)
    |
info: First overload defined here
   --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:149:9
    |
147 | … def keyClicks(self, widget: QtWidgets.QWidget|None, sequence: str|None, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
148 | … @typing.overload
149 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: QtCore.Qt.Key, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
150 | … @typing.overload
151 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: str, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |
info: Possible overloads for function `keyClick`:
info:   (self, widget: QWidget | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, widget: QWidget | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info: rule `no-matching-overload` was selected in the configuration file

error[no-matching-overload]: No overload of function `keyClick` matches arguments
   --> tests/e2e/review1_design.py:264:17
    |
262 |             for _ in range(len(buttons)):
263 |                 visited.add(app.focusWidget())
264 |                 QTest.keyClick(app.focusWidget(), QtCore.Qt.Key.Key_Right)
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
265 |                 app.processEvents()
266 |             assert visited == set(buttons), ("radio arrow traversal", visited, buttons)
    |
info: First overload defined here
   --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:149:9
    |
147 | … def keyClicks(self, widget: QtWidgets.QWidget|None, sequence: str|None, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
148 | … @typing.overload
149 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: QtCore.Qt.Key, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
150 | … @typing.overload
151 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: str, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |
info: Possible overloads for function `keyClick`:
info:   (self, widget: QWidget | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, widget: QWidget | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info: rule `no-matching-overload` was selected in the configuration file

error[no-matching-overload]: No overload of function `keyClick` matches arguments
   --> tests/e2e/review1_design.py:268:13
    |
266 |             assert visited == set(buttons), ("radio arrow traversal", visited, buttons)
267 |             radio.setFocus()
268 |             QTest.keyClick(radio, QtCore.Qt.Key.Key_Space)
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
269 |             app.processEvents()
270 |             assert radio.isChecked(), ("radio selection restoration", radio.text())
    |
info: First overload defined here
   --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:149:9
    |
147 | … def keyClicks(self, widget: QtWidgets.QWidget|None, sequence: str|None, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
148 | … @typing.overload
149 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: QtCore.Qt.Key, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
150 | … @typing.overload
151 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: str, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |
info: Possible overloads for function `keyClick`:
info:   (self, widget: QWidget | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, widget: QWidget | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info: rule `no-matching-overload` was selected in the configuration file

error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
   --> tests/e2e/ux_workflows.py:273:9
    |
271 |     assert form.error_label.text()
272 |     if app.platformName() in {"windows", "xcb", "cocoa"}:
273 |         QtTest.QTest.qWait(250)
    |         ^^^^^^^^^^^^^^^^^^^^^^^
274 |     assert form.rect().contains(button.mapTo(form, button.rect().bottomRight()))
275 |     assert form.rect().contains(form.error_label.mapTo(form, form.error_label.rect().bottomRight()))
    |
info: Parameter declared here
  --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:93:21
   |
91 |     @typing.overload
92 |     def qWaitForWindowActive(self, widget: QtWidgets.QWidget|None, timeout: int = ...) -> bool: ...
93 |     def qWait(self, ms: int) -> None: ...
   |                     ^^^^^^^
94 |     @typing.overload
95 |     def mouseRelease(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., …
   |
info: rule `missing-argument` was selected in the configuration file

error[invalid-argument-type]: Argument to function `qWait` is incorrect
   --> tests/e2e/ux_workflows.py:273:28
    |
271 |     assert form.error_label.text()
272 |     if app.platformName() in {"windows", "xcb", "cocoa"}:
273 |         QtTest.QTest.qWait(250)
    |                            ^^^ Expected `QTest`, found `Literal[250]`
274 |     assert form.rect().contains(button.mapTo(form, button.rect().bottomRight()))
275 |     assert form.rect().contains(form.error_label.mapTo(form, form.error_label.rect().bottomRight()))
    |
info: Function defined here
  --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:93:9
   |
91 |     @typing.overload
92 |     def qWaitForWindowActive(self, widget: QtWidgets.QWidget|None, timeout: int = ...) -> bool: ...
93 |     def qWait(self, ms: int) -> None: ...
   |         ^^^^^ ---- Parameter declared here
94 |     @typing.overload
95 |     def mouseRelease(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., …
   |
info: rule `invalid-argument-type` was selected in the configuration file

error[unresolved-attribute]: Attribute `setData` is not defined on `None` in union `QTableWidgetItem | None`
   --> tests/python/fast/test_calculator_qt6.py:483:9
    |
482 |     for column in (0, 1, 4, 5, 6):
483 |         form.simple_table.item(0, column).setData(QtCore.Qt.ItemDataRole.UserRole, True)
    |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
484 |     form.impute_data()
    |
info: rule `unresolved-attribute` was selected in the configuration file

Found 67 diagnostics

```
