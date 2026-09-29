# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Scalar workspace transforms compared with RCMetaR 0.4.1 output."""

import pytest

from rc_metastudio.meta_globals import BINARY, CONTINUOUS, DIAGNOSTIC
from rc_metastudio.workspace_scales import convert_scale


@pytest.mark.parametrize(
    ("value", "family", "metric", "direction", "n1", "expected"),
    (
        (1.5, BINARY, "OR", "calc.scale", None, 0.405465108108164),
        (0.4, BINARY, "OR", "display.scale", None, 1.491824697641270),
        (0.3, BINARY, "PLO", "calc.scale", None, -0.847297860387204),
        (0.4, BINARY, "PLO", "display.scale", None, 0.598687660112452),
        (0.3, BINARY, "PAS", "calc.scale", None, 0.579639740363704),
        (0.4, BINARY, "PAS", "display.scale", None, 0.151646645326417),
        (0.3, BINARY, "PFT", "calc.scale", 20, 0.589711175015508),
        (0.6, BINARY, "PFT", "display.scale", 20, 0.310010631597454),
        (0.3, DIAGNOSTIC, "Sens", "calc.scale", None, -0.847297860387204),
        (0.4, DIAGNOSTIC, "Sens", "display.scale", None, 0.598687660112452),
        (1.5, DIAGNOSTIC, "DOR", "calc.scale", None, 0.405465108108164),
        (0.3, CONTINUOUS, "SMD", "display.scale", None, 0.3),
    ),
)
def test_workspace_transform_matches_rcmetar_scalar_output(
    value, family, metric, direction, n1, expected
):
    assert convert_scale(value, family, metric, to=direction, n1=n1) == pytest.approx(
        expected, abs=1e-12
    )


def test_freeman_tukey_requires_denominator():
    with pytest.raises(ValueError, match="denominator"):
        convert_scale(0.5, BINARY, "PFT", to="display.scale")


def test_invalid_entered_ratios_do_not_store_infinite_effects():
    with pytest.raises(ValueError, match="greater than zero"):
        convert_scale(0.0, BINARY, "OR", to="calc.scale")
