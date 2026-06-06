# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Tests for port.cdm.oed_export — CDM-to-OED Location conversion (part 2).
"""

import csv
import io
import json
from pathlib import Path

import pytest

from port.cdm.oed_export import (
    _OED_FIELDS,
    cdm_to_oed_row,
    cdm_to_oed_rows,
    export_oed_csv,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_prop():
    p = Path(__file__).parent.parent.parent.parent / "src/port/cdm/asset/residential/sample_single_property.json"
    return json.loads(p.read_text())


@pytest.fixture()
def minimal_prop():
    """Minimal valid CDM record — only required fields."""
    return {
        "PropertyHeader": {
            "Header": {
                "PropertyID": "PROP-0001",
                "CatchmentID": "thames",
                "propertyType": "residential",
            },
            "Valuation": {"PropertyValue": 500_000.0},
            "PropertyAttributes": {},
            "Construction": {},
            "Location": {
                "LatitudeDegrees": 51.5,
                "LongitudeDegrees": -0.1,
            },
            "RiskAssessment": {},
            "ReferenceGauges": ["GAUGE-001"],
        },
        "ProtectionMeasures": {
            "RiskAssessment": {"GoverningBodyRatings": {}},
            "HazardProfile": {},
            "ResilienceMeasures": {},
        },
    }


# ---------------------------------------------------------------------------
# Derived fields
# ---------------------------------------------------------------------------

class TestDerivedFields:

    def test_street_address_combines_number_and_name(self, sample_prop):
        row = cdm_to_oed_row(sample_prop)
        assert "19" in row["StreetAddress"]
        assert "Oxford Road" in row["StreetAddress"]

    def test_flood_defense_height_when_barriers_present(self, sample_prop):
        # sample has DeployableBarriersProvided = "Partial"
        row = cdm_to_oed_row(sample_prop)
        assert row["FloodDefenseHeight"] == 1.0

    def test_flood_defense_height_absent_when_no_barriers(self, minimal_prop):
        row = cdm_to_oed_row(minimal_prop)
        assert row["FloodDefenseHeight"] == 0.0

    def test_perils_covered_default_when_no_hazard_profile(self, minimal_prop):
        row = cdm_to_oed_row(minimal_prop)
        assert row["LocPerilsCovered"] == "WF"

    def test_perils_covered_includes_active_hazards(self, minimal_prop):
        minimal_prop["ProtectionMeasures"]["HazardProfile"] = {
            "FloodHazardClass": "High",
            "WindHazardClass": "Medium",
            "SeismicHazardClass": "Low",
            "FireHazardClass": "None",
        }
        row = cdm_to_oed_row(minimal_prop)
        covered = row["LocPerilsCovered"].split(";")
        assert "WF" in covered
        assert "WSS" in covered
        assert "QEQ" not in covered


# ---------------------------------------------------------------------------
# BRI UserDef packing
# ---------------------------------------------------------------------------

class TestBriUserDef:

    def test_user_def1_is_bri_rating(self, sample_prop):
        row = cdm_to_oed_row(sample_prop)
        assert row["LocUserDef1"] == "NR"

    def test_user_def2_is_bri_score(self, sample_prop):
        row = cdm_to_oed_row(sample_prop)
        score = float(row["LocUserDef2"])
        assert 0.0 <= score <= 1.0

    def test_user_def3_four_sub_scores_pipe_delimited(self, sample_prop):
        row = cdm_to_oed_row(sample_prop)
        parts = row["LocUserDef3"].split("|")
        assert len(parts) == 4
        for p in parts:
            assert float(p) >= 0.0

    def test_user_def4_four_sub_ratings_pipe_delimited(self, sample_prop):
        row = cdm_to_oed_row(sample_prop)
        parts = row["LocUserDef4"].split("|")
        assert len(parts) == 4

    def test_user_def5_has_gauge_ids(self, sample_prop):
        row = cdm_to_oed_row(sample_prop)
        assert "GAUGE-" in row["LocUserDef5"]

    def test_user_def5_at_most_3_gauges(self, minimal_prop):
        minimal_prop["PropertyHeader"]["ReferenceGauges"] = [
            "G1", "G2", "G3", "G4", "G5"
        ]
        row = cdm_to_oed_row(minimal_prop)
        gauges = row["LocUserDef5"].split("|")
        assert len(gauges) <= 3

    def test_empty_bri_graceful(self, minimal_prop):
        row = cdm_to_oed_row(minimal_prop)
        assert row["LocUserDef1"] == ""
        assert row["LocUserDef2"] == "0.0"


# ---------------------------------------------------------------------------
# Bulk conversion
# ---------------------------------------------------------------------------

class TestBulkConversion:

    def test_cdm_to_oed_rows_returns_list(self, sample_prop):
        rows = cdm_to_oed_rows([sample_prop, sample_prop])
        assert len(rows) == 2

    def test_empty_input(self):
        assert cdm_to_oed_rows([]) == []


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

class TestCsvExport:

    def test_export_returns_string(self, sample_prop):
        content = export_oed_csv([sample_prop])
        assert isinstance(content, str)
        assert len(content) > 0

    def test_csv_has_header_row(self, sample_prop):
        content = export_oed_csv([sample_prop])
        reader = csv.DictReader(io.StringIO(content))
        assert set(reader.fieldnames or []) == set(_OED_FIELDS)

    def test_csv_data_row_count(self, sample_prop):
        content = export_oed_csv([sample_prop, sample_prop])
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        assert len(rows) == 2

    def test_export_to_file(self, sample_prop, tmp_path):
        out = tmp_path / "location.csv"
        content = export_oed_csv([sample_prop], path=out)
        assert out.exists()
        assert out.read_text() == content

    def test_loc_number_in_csv(self, sample_prop):
        content = export_oed_csv([sample_prop])
        reader = csv.DictReader(io.StringIO(content))
        row = next(reader)
        assert row["LocNumber"] == "PROP-e8b6e321"

    def test_building_tiv_in_csv(self, sample_prop):
        content = export_oed_csv([sample_prop])
        reader = csv.DictReader(io.StringIO(content))
        row = next(reader)
        assert float(row["BuildingTIV"]) == pytest.approx(1_516_677.72)
