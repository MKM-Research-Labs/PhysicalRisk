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

"""Shared helpers for mortgage generator tests."""

import json
from pathlib import Path


def write_property_portfolio(path: Path, count: int = 3) -> Path:
    """Seed a minimal property portfolio of `count` records for the active catchment.

    Persists through the ``database`` seam (so it lands in whatever backend the test
    bound — a tmp file under ``file``, Postgres under ``MKM_TEST_BACKEND=pg``); the
    raw ``property.json`` is also written for any file-coupled reader. Must be called
    inside the test's ``tmp_catchment`` so the active catchment + backend are bound.
    """
    import database

    properties = []
    for i in range(count):
        properties.append({
            "PropertyHeader": {
                "Header": {"PropertyID": f"PROP-{i:08x}"},
                "PropertyAttributes": {
                    "PropertyResi": "Flat",
                    "ConstructionYear": 1990 + i,
                    "PropertyCondition": "Good",
                },
                "Valuation": {"PropertyValue": 400000 + i * 50000},
                "Location": {
                    "PostCode": "SW1A 1AA",
                    "LatitudeDegrees": 51.5 + i * 0.01,
                    "LongitudeDegrees": -0.1 + i * 0.01,
                },
                "RiskAssessment": {"OverallFloodRisk": "Low"},
            }
        })
    data = {"properties": properties}
    database.save_properties(database.active_catchment(), data)   # seam (both backends)
    prop_path = path / "property.json"
    prop_path.write_text(json.dumps(data))
    return prop_path


def make_generator(tmp_path: Path):
    """Return a MortgagePortfolioGenerator with default config modules loaded.

    The WP2.4 generator no longer takes ``output_dir``; it reads the property portfolio
    and writes loans through ``database`` against the active catchment. Tests calling
    ``.generate()`` must run inside ``tmp_catchment(tmp_path)`` (their module fixture);
    ``tmp_path`` is kept in the signature for call-site compatibility."""
    from port.src.mortgage import MortgagePortfolioGenerator
    return MortgagePortfolioGenerator(verbose=False)
