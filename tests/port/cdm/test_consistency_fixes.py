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

"""Tests for builder._apply_consistency_fixes
(src/port/src/property/main/builder.py).

Covers the cross-field consistency post-step that runs after the schema-walker
populates a property record with independent random draws:

  - PropertyPeriod derived from ConstructionYear
  - NumberOfStoreys forced to 1 when PropertyResi == "Bungalow"
  - PropertyHeight reconciled with HeightMeters
  - County looked up from TownCity
  - OverallFloodRisk derived from EAFloodZone
  - PurchasePriceGbp derived from PropertyValue + PurchaseDate
  - SalePriceGbp derived from PropertyValue + SaleDate
  - RentalYield derived from MonthlyRentGbp + PropertyValue
  - MonthlyRentGbp / RentalYield cleared when RentalHistory == "Never rented"
  - LastFloodDateHistory cleared when FloodDamageSeverity == "No damage"
  - LastFireDate populated when FireDamageSeverity != "None"
"""

from datetime import date, timedelta

import pytest

from port.src.property.main.builder import (
    BuilderMixin, _period_from_year, _years_since,
)


def _fresh_mixin() -> BuilderMixin:
    """BuilderMixin is normally combined with LocationsMixin; the consistency
    method only needs self, so a bare instance works for unit testing."""
    return BuilderMixin()


def _scaffold(**overrides) -> dict:
    """Build a minimal property record with all the sub-sections the
    consistency fixer touches."""
    rec = {
        "PropertyHeader": {
            "PropertyAttributes": {
                "PropertyPeriod": "Pre-1919",  # deliberately wrong; will be derived
                "PropertyResi": "Detached",
                "NumberOfStoreys": 3,
                "ConstructionYear": 1980,
                "HeightMeters": 9.0,
            },
            "Construction": {"PropertyHeight": 4.0},  # also wrong; will sync
            "Location": {"TownCity": "Reading", "County": "Greater London"},
            "RiskAssessment": {"EAFloodZone": "Zone 1", "OverallFloodRisk": "High"},
            "Valuation": {"PropertyValue": 500000.0},
        },
        "TransactionHistory": {
            "Purchase": {"PurchaseDate": "2020-01-15", "PurchasePriceGbp": 10.0},
            "Sales":    {"SaleDate":    "2018-06-20", "SalePriceGbp":    10.0},
            "Rental":   {"MonthlyRentGbp": 2000, "RentalYield": 9.99, "RentalHistory": "Currently rented"},
        },
        "HistoryAndIncidents": {
            "FloodEvents":    {"FloodDamageSeverity": "No damage", "LastFloodDateHistory": "2015-09-13"},
            "FireIncidents":  {"FireDamageSeverity": "Severe"},  # no LastFireDate
        },
    }
    # Apply caller overrides at top level (e.g. overrides={"Valuation": {...}})
    for k, v in overrides.items():
        rec["PropertyHeader"].setdefault(k, {}).update(v) if k != "TransactionHistory" else rec[k].update(v)
    return rec


# ---------------------------------------------------------------------------
# _period_from_year
# ---------------------------------------------------------------------------

class TestPeriodFromYear:

    @pytest.mark.parametrize("year,expected", [
        (1850, "Pre-1919"),
        (1918, "Pre-1919"),
        (1919, "1919-1944"),
        (1944, "1919-1944"),
        (1945, "1945-1975"),
        (1975, "1945-1975"),
        (1976, "1976-1999"),
        (1999, "1976-1999"),
        (2000, "2000-2008"),
        (2008, "2000-2008"),
        (2009, "2009-Present"),
        (2025, "2009-Present"),
    ])
    def test_boundaries(self, year, expected):
        assert _period_from_year(year) == expected


# ---------------------------------------------------------------------------
# _years_since
# ---------------------------------------------------------------------------

class TestYearsSince:

    def test_recent_date_returns_positive_fraction(self):
        d = (date.today() - timedelta(days=365 * 3)).isoformat()
        assert _years_since(d) == pytest.approx(3.0, abs=0.01)

    def test_iso_with_time_component(self):
        d = (date.today() - timedelta(days=365 * 2)).isoformat() + "T12:34:56"
        assert _years_since(d) == pytest.approx(2.0, abs=0.01)

    def test_none_input(self):
        assert _years_since(None) is None

    def test_bad_string(self):
        assert _years_since("not a date") is None

    def test_datetime_instance(self):
        from datetime import datetime
        dt = datetime.now() - timedelta(days=365)
        assert _years_since(dt) == pytest.approx(1.0, abs=0.01)

    def test_date_instance(self):
        d = date.today() - timedelta(days=365 * 4)
        assert _years_since(d) == pytest.approx(4.0, abs=0.01)

    def test_unsupported_type_returns_none(self):
        # Integers/other types fall through to the `else: return None` branch.
        assert _years_since(12345) is None
        assert _years_since([2020, 1, 1]) is None

    def test_future_date_clamped_to_zero(self):
        # Negative interval clamps to 0.0, not negative.
        d = (date.today() + timedelta(days=365)).isoformat()
        assert _years_since(d) == 0.0


# ---------------------------------------------------------------------------
# _apply_consistency_fixes — individual rules
# ---------------------------------------------------------------------------

class TestConsistencyFixes:

    def test_property_period_derived_from_construction_year(self):
        rec = _scaffold()
        rec["PropertyHeader"]["PropertyAttributes"]["ConstructionYear"] = 1968
        _fresh_mixin()._apply_consistency_fixes(rec)
        assert rec["PropertyHeader"]["PropertyAttributes"]["PropertyPeriod"] == "1945-1975"

    def test_bungalow_forced_to_single_storey(self):
        rec = _scaffold()
        rec["PropertyHeader"]["PropertyAttributes"]["PropertyResi"] = "Bungalow"
        rec["PropertyHeader"]["PropertyAttributes"]["NumberOfStoreys"] = 4
        _fresh_mixin()._apply_consistency_fixes(rec)
        assert rec["PropertyHeader"]["PropertyAttributes"]["NumberOfStoreys"] == 1

    def test_property_height_synced_to_height_meters(self):
        rec = _scaffold()
        rec["PropertyHeader"]["PropertyAttributes"]["HeightMeters"] = 22.8
        rec["PropertyHeader"]["Construction"]["PropertyHeight"] = 4.0
        _fresh_mixin()._apply_consistency_fixes(rec)
        assert rec["PropertyHeader"]["Construction"]["PropertyHeight"] == 22.8

    @pytest.mark.parametrize("town,expected_county", [
        ("Reading", "Berkshire"),
        ("Slough", "Berkshire"),
        ("Oxford", "Oxfordshire"),
        ("Henley-on-Thames", "Oxfordshire"),
        ("Westminster", "Greater London"),
        ("London", "Greater London"),
    ])
    def test_county_lookup(self, town, expected_county):
        rec = _scaffold()
        rec["PropertyHeader"]["Location"]["TownCity"] = town
        rec["PropertyHeader"]["Location"]["County"] = "WRONG"
        _fresh_mixin()._apply_consistency_fixes(rec)
        assert rec["PropertyHeader"]["Location"]["County"] == expected_county

    def test_unknown_town_keeps_county(self):
        rec = _scaffold()
        rec["PropertyHeader"]["Location"]["TownCity"] = "NoSuchTown"
        rec["PropertyHeader"]["Location"]["County"] = "Original County"
        _fresh_mixin()._apply_consistency_fixes(rec)
        assert rec["PropertyHeader"]["Location"]["County"] == "Original County"

    @pytest.mark.parametrize("zone,expected", [
        ("Zone 1", "Low"),
        ("Zone 2", "Medium"),
        ("Zone 3a", "High"),
        ("Zone 3b", "Very high"),
    ])
    def test_overall_flood_risk_from_zone(self, zone, expected):
        rec = _scaffold()
        rec["PropertyHeader"]["RiskAssessment"]["EAFloodZone"] = zone
        rec["PropertyHeader"]["RiskAssessment"]["OverallFloodRisk"] = "WRONG"
        _fresh_mixin()._apply_consistency_fixes(rec)
        assert rec["PropertyHeader"]["RiskAssessment"]["OverallFloodRisk"] == expected

    def test_purchase_price_discounted_by_years_since(self):
        rec = _scaffold()
        rec["PropertyHeader"]["Valuation"]["PropertyValue"] = 1_000_000.0
        rec["TransactionHistory"]["Purchase"]["PurchaseDate"] = (
            (date.today() - timedelta(days=365 * 5)).isoformat()
        )
        _fresh_mixin()._apply_consistency_fixes(rec)
        # 1.04^5 ≈ 1.2167 → discounted price ≈ 821,927
        pp = rec["TransactionHistory"]["Purchase"]["PurchasePriceGbp"]
        assert 800_000 < pp < 850_000

    def test_sale_price_discounted_by_years_since(self):
        rec = _scaffold()
        rec["PropertyHeader"]["Valuation"]["PropertyValue"] = 500_000.0
        rec["TransactionHistory"]["Sales"]["SaleDate"] = (
            (date.today() - timedelta(days=365 * 2)).isoformat()
        )
        _fresh_mixin()._apply_consistency_fixes(rec)
        sp = rec["TransactionHistory"]["Sales"]["SalePriceGbp"]
        # 500000 / 1.04^2 ≈ 462,278
        assert 450_000 < sp < 475_000

    def test_rental_yield_derived(self):
        rec = _scaffold()
        rec["PropertyHeader"]["Valuation"]["PropertyValue"] = 500_000.0
        rec["TransactionHistory"]["Rental"]["MonthlyRentGbp"] = 2_500.0
        rec["TransactionHistory"]["Rental"]["RentalHistory"] = "Currently rented"
        _fresh_mixin()._apply_consistency_fixes(rec)
        # 2500 * 12 / 500000 * 100 = 6.0
        assert rec["TransactionHistory"]["Rental"]["RentalYield"] == pytest.approx(6.0)

    def test_never_rented_clears_rental_fields(self):
        rec = _scaffold()
        rec["TransactionHistory"]["Rental"]["RentalHistory"] = "Never rented"
        rec["TransactionHistory"]["Rental"]["MonthlyRentGbp"] = 9999
        rec["TransactionHistory"]["Rental"]["RentalYield"] = 8.88
        _fresh_mixin()._apply_consistency_fixes(rec)
        assert rec["TransactionHistory"]["Rental"]["MonthlyRentGbp"] is None
        assert rec["TransactionHistory"]["Rental"]["RentalYield"] is None

    def test_no_damage_clears_last_flood_date(self):
        rec = _scaffold()
        rec["HistoryAndIncidents"]["FloodEvents"]["FloodDamageSeverity"] = "No damage"
        rec["HistoryAndIncidents"]["FloodEvents"]["LastFloodDateHistory"] = "2015-09-13"
        _fresh_mixin()._apply_consistency_fixes(rec)
        assert rec["HistoryAndIncidents"]["FloodEvents"]["LastFloodDateHistory"] is None

    def test_severe_fire_gets_a_date(self):
        rec = _scaffold()
        rec["HistoryAndIncidents"]["FireIncidents"]["FireDamageSeverity"] = "Severe"
        rec["HistoryAndIncidents"]["FireIncidents"].pop("LastFireDate", None)
        _fresh_mixin()._apply_consistency_fixes(rec)
        d = rec["HistoryAndIncidents"]["FireIncidents"]["LastFireDate"]
        assert d is not None and len(d) == 10  # YYYY-MM-DD

    def test_none_fire_severity_leaves_date_alone(self):
        rec = _scaffold()
        rec["HistoryAndIncidents"]["FireIncidents"]["FireDamageSeverity"] = "None"
        rec["HistoryAndIncidents"]["FireIncidents"].pop("LastFireDate", None)
        _fresh_mixin()._apply_consistency_fixes(rec)
        # Should not invent a date for a property that didn't have a fire.
        assert rec["HistoryAndIncidents"]["FireIncidents"].get("LastFireDate") is None
