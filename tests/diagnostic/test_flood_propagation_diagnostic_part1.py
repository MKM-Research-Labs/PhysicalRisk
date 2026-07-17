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

"""
Diagnostic test: trace flood propagation from gauge to property — Part 1.

Covers gauge-level storm responses and property nearest gauge assignment.

Run: pytest tests/diagnostic/test_flood_propagation_diagnostic_part1.py -v -s
"""

import pytest


# -----------------------------------------------------------------------
# 1. Gauge-level: do storms actually produce high WSE at gauges?
# -----------------------------------------------------------------------

class TestGaugeLevelStorms:
    """Verify that storm responses exist and produce meaningful peaks."""

    def test_gaugets_have_storm_responses(self, gaugets):
        """Every gaugets file should have storm_responses with responses."""
        missing = []
        for gid, data in gaugets.items():
            sr = data.get('storm_responses', {})
            if isinstance(sr, dict):
                responses = sr.get('responses', [])
            else:
                responses = sr
            if len(responses) == 0:
                missing.append(gid)
        assert len(missing) == 0, (
            f"{len(missing)} gaugets files have no storm responses: {missing[:5]}"
        )

    def test_some_storms_exceed_alert(self, gaugets):
        """At least some storms should exceed alert threshold."""
        total_alert = 0
        total_storms = 0
        for gid, data in gaugets.items():
            sr = data.get('storm_responses', {})
            responses = sr.get('responses', []) if isinstance(sr, dict) else sr
            total_storms += len(responses)
            for r in responses:
                if r.get('exceeded_alert', False):
                    total_alert += 1
        pct = total_alert / total_storms * 100 if total_storms > 0 else 0
        assert total_alert > 0, "No storms exceed alert at any gauge"
        print(f"\n  Alert-breaching storms: {total_alert}/{total_storms} ({pct:.1f}%)")

    def test_gaugets_have_flood_simulation(self, gaugets):
        """Every gaugets file should have 168-hour flood simulation."""
        missing = []
        for gid, data in gaugets.items():
            readings = data.get('flood_simulation', {}).get('readings', [])
            if len(readings) != 168:
                missing.append((gid, len(readings)))
        assert len(missing) == 0, (
            f"{len(missing)} gaugets missing 168h readings: {missing[:5]}"
        )

    def test_synth_gaugets_have_responses(self, gaugets):
        """Synthetic gaugets specifically should have storm responses."""
        synth_gaugets = {k: v for k, v in gaugets.items() if k.startswith('SYNTH-')}
        assert len(synth_gaugets) > 0, "No SYNTH-* gaugets found"
        for gid, data in synth_gaugets.items():
            sr = data.get('storm_responses', {})
            responses = sr.get('responses', []) if isinstance(sr, dict) else sr
            assert len(responses) > 0, f"{gid} has no storm responses"
            alerts = sum(1 for r in responses if r.get('exceeded_alert', False))
            print(f"\n  {gid}: {len(responses)} responses, {alerts} alert-breaching")


# -----------------------------------------------------------------------
# 2. Property-level: are nearest gauges populated correctly?
# -----------------------------------------------------------------------

class TestPropertyNearestGauges:
    """Verify nearest gauge assignment and elevation data."""

    def test_all_properties_have_nearest_gauges(self, properties):
        missing = [pid for pid, p in properties.items()
                   if len(p.get('nearest_gauges', [])) == 0]
        assert len(missing) == 0, f"{len(missing)} properties have no nearest gauges"

    def test_nearest_gauges_have_elevation(self, properties):
        """Every nearest gauge should have gauge_elevation_m."""
        bad = []
        for pid, p in properties.items():
            for ng in p.get('nearest_gauges', []):
                elev = ng.get('gauge_elevation_m')
                if elev is None or elev == 0:
                    bad.append((pid, ng.get('gauge_id', '?'), elev))
        assert len(bad) == 0, (
            f"{len(bad)} nearest-gauge entries missing elevation: {bad[:5]}"
        )

    def test_at_most_one_synthetic_gauge(self, properties):
        """Each property should have at most 1 synthetic gauge."""
        bad = []
        for pid, p in properties.items():
            synth_count = sum(1 for ng in p.get('nearest_gauges', [])
                              if ng['gauge_id'].startswith('SYNTH-'))
            if synth_count > 1:
                bad.append((pid, synth_count))
        assert len(bad) == 0, f"{len(bad)} properties have >1 synthetic gauge: {bad[:5]}"
