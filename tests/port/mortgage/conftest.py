# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
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
    """Write a minimal property.json with `count` synthetic property records."""
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
    prop_path = path / "property.json"
    prop_path.write_text(json.dumps(data))
    return prop_path


def make_generator(tmp_path: Path):
    """Return a MortgagePortfolioGenerator with default config modules loaded."""
    from port.src.mortgage import MortgagePortfolioGenerator
    return MortgagePortfolioGenerator(output_dir=tmp_path, verbose=False)
