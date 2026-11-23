import math
import os
import sys

import pytest


sys.path.insert(0, os.path.abspath("src"))

from rc_metastudio.analysis.validation import normalize_confidence_level_params, is_valid_plot_tick_list, validate_analysis_digits, validate_correction_factor, validate_confidence_level
from rc_metastudio.analysis.catalog import CONTINUOUS
from rc_metastudio.project.model import Arm, Sheet
from rc_metastudio.project.study import AnalysisUnit
from rc_metastudio.domain_ids import ArmId, SheetId


def test_plot_ticks_accept_only_comma_separated_finite_numbers():
    assert is_valid_plot_tick_list("-1.5, 0, 2e3")
    assert not is_valid_plot_tick_list("1")
    assert not is_valid_plot_tick_list("1, inf")
    assert not is_valid_plot_tick_list("1, __import__('os').getcwd()")


def test_validate_confidence_level_rejects_endpoints_and_non_finite_values():
    for value in (0, 100, -1, 101, math.inf, -math.inf, math.nan, None, "bad"):
        with pytest.raises(ValueError, match="greater than 0 and less than 100"):
            validate_confidence_level(value)


@pytest.mark.parametrize("level,multiplier", [
    (90.0, 1.6448536269514729),
    (95.0, 1.959963984540054),
    (math.nextafter(100.0, 0.0), 8.292361075813597),
])
def test_entered_interval_uses_its_original_confidence_for_standard_error(level, multiplier):
    sheet = Sheet(
        SheetId("effect"), "Effect", CONTINUOUS, sub_type="means",
        arms=[Arm(ArmId("a"), "Group A"), Arm(ArmId("b"), "Group B")],
    )
    sheet.settings["confidence_level"] = level
    unit = AnalysisUnit(sheet)
    arms = tuple(arm.stable_id for arm in unit.arms.values())
    unit.set_effect("MD", arms, 2.0)
    unit.set_lower("MD", arms, 1.0)
    unit.set_upper("MD", arms, 3.0)

    sheet.settings["confidence_level"] = 80.0
    assert unit.get_entered_effect_and_ci("MD", arms) == (2.0, 1.0, 3.0)
    assert unit.get_se("entered", "MD", arms, 1.2815515655446004) == pytest.approx(1 / multiplier)


def test_normalize_confidence_level_params_rejects_invalid_analysis_dictionaries():
    with pytest.raises(ValueError, match="greater than 0 and less than 100"):
        normalize_confidence_level_params({"conf.level": 100, "digits": 3})


def test_validate_analysis_digits_rejects_negative_and_non_integer_values():
    for value in (-1, "-5", 1.5, "2.5", math.inf, math.nan, None, "bad"):
        with pytest.raises(ValueError, match="Decimal places"):
            validate_analysis_digits(value)


def test_normalize_confidence_level_params_rejects_invalid_digits():
    with pytest.raises(ValueError, match="Decimal places"):
        normalize_confidence_level_params({"conf.level": 95, "digits": -5})


def test_validate_correction_factor_rejects_negative_and_non_finite_values():
    for value in (-0.1, math.inf, math.nan, None, "bad"):
        with pytest.raises(ValueError, match="Correction factor"):
            validate_correction_factor(value)


def test_normalize_confidence_level_params_validates_reitsma_controls():
    assert normalize_confidence_level_params(
        {"conf.level": "99.9", "digits": "3", "adjust": "0.5"}
    ) == {"conf.level": 99.9, "digits": 3, "adjust": 0.5}
