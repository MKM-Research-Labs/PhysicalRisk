# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Energy-intensity benchmark bands on the property energy page.

Five bands, keyed off kWh per square metre per year. Three of the five had no
test, including both ends — the band boundaries are what a reader acts on, so
an off-by-one in the ladder mislabels a property's consumption.
"""

import pytest

from reports.property.property_page_08_energy import EnergyPage


def _record(annual_kwh, area_sqm):
    return {
        "PropertyHeader": {
            "Header": {"PropertyID": "PROP-001"},
            "PropertyAttributes": {"PropertyAreaSqm": area_sqm},
        },
        "EnergyPerformance": {
            "EnergyUsage": {"AnnualEnergyKwh": annual_kwh},
        },
    }


def _intensity_rating(annual_kwh, area_sqm):
    elements = EnergyPage().generate_elements(_record(annual_kwh, area_sqm))
    for e in elements:
        rows = getattr(e, "_cellvalues", None)
        if not rows:
            continue
        for row in rows:
            if row and row[0] == "Intensity Rating":
                return row[1]
    return None


@pytest.mark.parametrize("intensity,expected", [
    (250, "High - Above average consumption"),
    (175, "Medium-High - Moderate consumption"),
    (125, "Average - Typical consumption"),
    (75, "Good - Below average consumption"),
    (25, "Excellent - Very low consumption"),
])
def test_each_band_is_labelled(intensity, expected):
    """One square metre, so annual kWh is the intensity."""
    assert _intensity_rating(intensity, 1) == expected


@pytest.mark.parametrize("boundary,expected", [
    (200, "Medium-High - Moderate consumption"),
    (150, "Average - Typical consumption"),
    (100, "Good - Below average consumption"),
    (50, "Excellent - Very low consumption"),
])
def test_the_boundaries_fall_to_the_lower_band(boundary, expected):
    """Every comparison is a strict `>`, so a value sitting exactly on a
    threshold belongs to the band below it. Pinned because a later edit to
    `>=` would silently reclassify every property on a boundary."""
    assert _intensity_rating(boundary, 1) == expected


def test_no_area_means_no_intensity_row():
    """Intensity is undefined without a floor area, and must not be guessed."""
    assert _intensity_rating(5000, None) is None
    assert _intensity_rating(5000, 0) is None
