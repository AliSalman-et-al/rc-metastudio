"""Failure modes of the numeric result boundary (no display-text parsing)."""
import math
import pytest
from rc_metastudio.analysis_results import Quantity, ResultTable


@pytest.mark.parametrize('fields', [
    {'role': 'unknown', 'value': 1.0},
    {'role': 'estimate', 'value': True},
    {'role': 'estimate', 'value': float('nan')},
    {'role': 'estimate', 'value': 1.0, 'scale': 'unknown'},
    {'role': 'p', 'value': .1, 'level': 95.0},
    {'role': 'ci_lower', 'value': .1},
    {'role': 'pi_upper', 'value': .1, 'level': 100.0},
    {'role': 'ci_upper', 'value': .1, 'level': 0.0},
])
def test_invalid_quantity_rejected(fields):
    with pytest.raises(ValueError):
        Quantity(**fields)


def test_raw_states_and_combined_interval_are_preserved():
    lower = Quantity('ci_lower', 1e-19, 'display', 90.0)
    upper = Quantity('ci_upper', math.inf, 'display', 90.0)
    missing = Quantity('estimate', None)
    table = ResultTable('Raw', ('CI', 'Estimate'), (('0.000 to —', 'Not estimable'),),
                        (((lower, upper), (missing,)),))
    assert table.quantities[0][0] == (lower, upper)
    assert table.quantities[0][1][0].value is None
    assert table.quantities[0][0][0].value == 1e-19


@pytest.mark.parametrize('quantities', [(((Quantity('value', 1.0),),),),
                                       ((), ()), ((("fake",), ()),)])
def test_misaligned_or_untyped_quantity_rejected(quantities):
    with pytest.raises(ValueError):
        ResultTable('Bad', ('A', 'B'), (('a', 'b'),), quantities)
