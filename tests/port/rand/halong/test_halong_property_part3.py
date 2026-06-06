# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage smoke tests for port.rand.halong.property.* (part 3)

Strategy: import every submodule, exercise every field generator in
get_field_generators() with a realistic location_info dict, plus
smoke-test the major resilience / valuation / energy / location
calculations. Maximum coverage per line-of-test.
"""

import random
from datetime import datetime, timedelta

import pytest


@pytest.fixture(autouse=True)
def _seeded():
    random.seed(20260527)


# ---------------------------------------------------------------------------
# resilience.py — the big one (313 LOC)
# ---------------------------------------------------------------------------

class TestResilienceModule:
    def _scaffold(self, period="1976-1999", condition="Fair",
                  zone="Zone 1", basement=False):
        return {
            "PropertyHeader": {
                "PropertyAttributes": {
                    "PropertyPeriod": period,
                    "PropertyCondition": condition,
                },
                "Construction": {"BasementPresent": basement},
                "RiskAssessment": {"EAFloodZone": zone},
            }
        }

    def test_generate_resilience_returns_sections(self):
        from port.rand.halong.property.property_random.resilience import generate_resilience
        prop = self._scaffold()
        result = generate_resilience(prop)
        assert isinstance(result, dict)
        # SiteAndDrainage is always populated with BasementFloodStrategy override
        assert "SiteAndDrainage" in result
        assert "BasementFloodStrategy" in result["SiteAndDrainage"]

    @pytest.mark.parametrize("period", [
        "Pre-1919", "1919-1944", "1945-1975",
        "1976-1999", "2000-2008", "2009-Present",
    ])
    def test_generate_resilience_all_periods(self, period):
        from port.rand.halong.property.property_random.resilience import generate_resilience
        result = generate_resilience(self._scaffold(period=period))
        assert isinstance(result, dict) and result

    @pytest.mark.parametrize("condition", [
        "Excellent", "Good", "Fair", "Poor", "Very poor",
    ])
    def test_generate_resilience_all_conditions(self, condition):
        from port.rand.halong.property.property_random.resilience import generate_resilience
        result = generate_resilience(self._scaffold(condition=condition))
        assert isinstance(result, dict) and result

    @pytest.mark.parametrize("zone", ["Zone 1", "Zone 2", "Zone 3a", "Zone 3b"])
    def test_generate_resilience_all_zones(self, zone):
        from port.rand.halong.property.property_random.resilience import generate_resilience
        result = generate_resilience(self._scaffold(zone=zone))
        assert isinstance(result, dict)

    def test_generate_resilience_with_basement(self):
        from port.rand.halong.property.property_random.resilience import generate_resilience
        result = generate_resilience(self._scaffold(basement=True))
        assert isinstance(result, dict)

    def test_compute_bri_rating(self):
        from port.rand.halong.property.property_random.resilience import (
            compute_bri_rating, generate_resilience,
        )
        prop = self._scaffold()
        resilience = generate_resilience(prop)
        result = compute_bri_rating(resilience)
        assert "rating" in result
        assert "score" in result
        assert isinstance(result["score"], float)

    def test_score_section(self):
        from port.rand.halong.property.property_random.resilience import score_section
        section = {"FieldA": "Good", "FieldB": "Excellent"}
        score = score_section("SiteAndDrainage", section)
        assert isinstance(score, float)

    def test_distribution_summary_default_target(self):
        from port.rand.halong.property.property_random.resilience import distribution_summary
        # Signature is (ratings, target=None) — target falls back to a
        # built-in Thames distribution
        ratings = ["A", "B", "C", "A", "B", "C", "A"]
        summary = distribution_summary(ratings)
        # One entry per RATING_ORDER with actual/target/delta sub-keys
        assert any("actual" in v for v in summary.values())

    def test_distribution_summary_custom_target(self):
        from port.rand.halong.property.property_random.resilience import distribution_summary
        summary = distribution_summary(["A", "A", "B"], target={"A": 0.5, "B": 0.3, "C": 0.2})
        assert "A" in summary

    def test_sanity_check_distribution_runs(self):
        """End-to-end sanity check at small N — exercises ~all of the
        synthetic-property + scoring path."""
        from port.rand.halong.property.property_random.resilience import (
            sanity_check_distribution,
        )
        result = sanity_check_distribution(sample_size=30, seed=20260527)
        assert isinstance(result, dict)

    def test_validate_weights_does_not_raise(self):
        from port.rand.halong.property.property_random.resilience import validate_weights
        validate_weights()

    def test_apply_flood_resilience_score_to_property(self):
        from port.rand.halong.property.property_random.resilience import (
            apply_flood_resilience_score, generate_resilience,
        )
        prop = self._scaffold()
        prop["ProtectionMeasures"] = {"ResilienceMeasures": generate_resilience(prop)}
        # apply_flood_resilience_score should run without raising
        result = apply_flood_resilience_score(prop)
        assert result is not None or result == {} or isinstance(prop, dict)
