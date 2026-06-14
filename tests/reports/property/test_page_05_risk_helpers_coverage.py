# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage tests for the risk-assessment Vs30 -> NEHRP site-class mapping."""

import pytest

from reports.property.property_page_05_risk_assessment._helpers import (
    _RiskHelpersMixin,
)


@pytest.mark.parametrize("vs30,expected", [
    (900, "Rock (Site Class A/B)"),
    (760, "Rock (Site Class A/B)"),
    (500, "Stiff soil (Site Class C)"),
    (360, "Stiff soil (Site Class C)"),
    (250, "Soft soil (Site Class D)"),
    (180, "Soft soil (Site Class D)"),
    (100, "Very soft soil (Site Class E)"),
    (0, "Very soft soil (Site Class E)"),
])
def test_vs30_site_class(vs30, expected):
    assert _RiskHelpersMixin()._vs30_site_class(vs30) == expected  # lines 56-63
