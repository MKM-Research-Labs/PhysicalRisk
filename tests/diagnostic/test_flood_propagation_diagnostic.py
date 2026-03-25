"""
Diagnostic test: trace flood propagation from gauge to property.

This test loads real data and traces the EXACT computation chain to
identify where flood signal is being lost.  Written 25-Mar-2026 after
discovering 0 flood events at properties despite strong gauge signals.

Run: pytest tests/diagnostic/test_flood_propagation_diagnostic.py -v -s
"""

import json
import math
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).resolve().parents[2] / 'data' / 'input' / 'thames'


def _load_json(path):
    with open(path) as f:
        return json.load(f)


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------

@pytest.fixture(scope="module")
def gauge_json():
    return _load_json(DATA_DIR / 'gauge.json')


@pytest.fixture(scope="module")
def gaugets():
    result = {}
    gaugets_dir = DATA_DIR / 'gaugets'
    for f in gaugets_dir.glob('*.json'):
        data = _load_json(f)
        result[f.stem] = data
    return result


@pytest.fixture(scope="module")
def properties():
    result = {}
    pts_dir = DATA_DIR / 'propertyts'
    for f in pts_dir.glob('PROP-*.json'):
        data = _load_json(f)
        result[data['property_id']] = data
    return result


@pytest.fixture(scope="module")
def gaugehc():
    return _load_json(DATA_DIR / 'gaugehc.json')


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


# -----------------------------------------------------------------------
# 3. Flood propagation: trace the exact math for specific properties
# -----------------------------------------------------------------------

class TestFloodPropagationMath:
    """Trace the flood computation step by step to find where signal drops."""

    def _get_property_with_high_gauge_signal(self, properties, gaugets):
        """Find a property whose nearest gauge has alert-breaching storms."""
        for pid, p in properties.items():
            for ng in p.get('nearest_gauges', []):
                gid = ng['gauge_id']
                gt = gaugets.get(gid, {})
                sr = gt.get('storm_responses', {})
                responses = sr.get('responses', []) if isinstance(sr, dict) else sr
                alerts = [r for r in responses if r.get('exceeded_alert', False)]
                if len(alerts) > 10:
                    return pid, p, ng, gt, alerts
        return None, None, None, None, None

    def test_property_receives_gauge_alert_storms(self, properties, gaugets):
        """At least one property should have a nearest gauge with alert storms."""
        pid, p, ng, gt, alerts = self._get_property_with_high_gauge_signal(
            properties, gaugets)
        assert pid is not None, "No property found with nearby alert-breaching gauge"
        print(f"\n  Property {pid}: gauge {ng['gauge_id']} has {len(alerts)} alert storms")

    def test_idw_produces_high_wse(self, properties, gaugets):
        """The IDW interpolation should produce high WSE from alert storms."""
        pid, p, ng, gt, alerts = self._get_property_with_high_gauge_signal(
            properties, gaugets)
        if pid is None:
            pytest.skip("No suitable property found")

        # Get the highest alert storm peak
        max_peak = max(a.get('peak_level_m', 0) for a in alerts)
        print(f"\n  Gauge {ng['gauge_id']}: max peak_level_m = {max_peak:.3f}")
        print(f"  Property elevation: {p['elevation_m']}m, floor: {p['floor_level_m']}m")

        # Check if this peak would flood the property
        g_elev = ng.get('gauge_elevation_m', 0)
        retention = math.exp(-ng['distance_m'] / 10000.0)
        water_above = max(0, max_peak - g_elev)
        water_at_prop = water_above * retention
        height_diff = max(0, p['elevation_m'] - g_elev)
        threshold = height_diff + p['floor_level_m']
        est_depth = max(0, water_at_prop - threshold)

        print(f"  Gauge elevation: {g_elev}m")
        print(f"  water_above_gauge = {max_peak:.3f} - {g_elev} = {water_above:.3f}m")
        print(f"  retention = exp(-{ng['distance_m']:.0f}/10000) = {retention:.4f}")
        print(f"  water_at_property = {water_above:.3f} * {retention:.4f} = {water_at_prop:.3f}m")
        print(f"  height_diff = {p['elevation_m']} - {g_elev} = {height_diff:.2f}m")
        print(f"  threshold = {height_diff:.2f} + {p['floor_level_m']} = {threshold:.2f}m")
        print(f"  estimated_depth = {water_at_prop:.3f} - {threshold:.2f} = {est_depth:.3f}m")

        assert water_at_prop > 0, "IDW/retention produced zero water at property"

    def test_flood_events_match_expectation(self, properties, gaugets):
        """Properties with est_depth > 0 should have some flooded events."""
        pid, p, ng, gt, alerts = self._get_property_with_high_gauge_signal(
            properties, gaugets)
        if pid is None:
            pytest.skip("No suitable property found")

        g_elev = ng.get('gauge_elevation_m', 0)
        retention = math.exp(-ng['distance_m'] / 10000.0)
        height_diff = max(0, p['elevation_m'] - g_elev)
        threshold = height_diff + p['floor_level_m']

        expected_floods = 0
        for a in alerts:
            peak = a.get('peak_level_m', 0)
            water_above = max(0, peak - g_elev)
            water_at_prop = water_above * retention
            if water_at_prop > threshold:
                expected_floods += 1

        actual_floods = sum(1 for e in p.get('flood_events', [])
                           if e.get('flooded', False))

        print(f"\n  Expected floods (from math): {expected_floods}")
        print(f"  Actual floods (in data): {actual_floods}")
        print(f"  Total events in file: {len(p.get('flood_events', []))}")

        if expected_floods > 0 and actual_floods == 0:
            # This is the bug — show the top event for debugging
            events = p.get('flood_events', [])
            top = sorted(events, key=lambda e: e.get('interpolated_wse_m', 0),
                         reverse=True)[:3]
            print("\n  TOP 3 EVENTS (should flood but don't):")
            for e in top:
                print(f"    storm={e['storm_id'][:16]}, "
                      f"interp_wse={e.get('interpolated_wse_m', 0):.3f}, "
                      f"atten_wse={e.get('attenuated_wse_m', 0):.3f}, "
                      f"depth={e.get('flood_depth_m', 0):.3f}, "
                      f"retention={e.get('retention_factor', 0):.4f}")

            pytest.fail(
                f"Property {pid} should have {expected_floods} floods "
                f"but has {actual_floods}. The flood propagation chain is broken."
            )

    def test_build_property_hydrograph_produces_depth(self, gaugets, properties):
        """Directly call build_property_hydrograph and verify it produces depth."""
        from models.floodrisk.velocity import build_property_hydrograph

        pid, p, ng, gt, alerts = self._get_property_with_high_gauge_signal(
            properties, gaugets)
        if pid is None:
            pytest.skip("No suitable property found")

        # Get gauge readings
        gauge_readings_raw = gt.get('flood_simulation', {}).get('readings', [])
        mapped_readings = []
        for idx, r in enumerate(gauge_readings_raw):
            mapped_readings.append({
                'hour': r.get('hour', idx),
                'water_level_m': r.get('waterLevel', r.get('water_level_m', 0)),
            })

        # Get highest alert storm
        best_alert = max(alerts, key=lambda a: a.get('peak_level_m', 0))
        peak_wse = best_alert['peak_level_m']

        g_elev = ng.get('gauge_elevation_m', 0)
        retention = math.exp(-ng['distance_m'] / 10000.0)

        # Compute travel time
        from models.floodrisk.velocity import compute_travel_time, compute_slope
        slope = compute_slope(g_elev, p['elevation_m'], ng['distance_m'])
        water_above = max(0, peak_wse - g_elev)
        water_at_prop = water_above * retention
        height_diff = max(0, p['elevation_m'] - g_elev)
        threshold = height_diff + p['floor_level_m']
        est_depth = max(0, water_at_prop - threshold)
        travel_time = compute_travel_time(ng['distance_m'], est_depth, slope) if est_depth > 0 else 0
        if travel_time == float('inf'):
            travel_time = 0

        print(f"\n  Calling build_property_hydrograph:")
        print(f"    gauge readings: {len(mapped_readings)}")
        print(f"    peak_wse: {peak_wse:.3f}")
        print(f"    travel_time: {travel_time:.2f}hrs")
        print(f"    retention: {retention:.4f}")
        print(f"    prop_elevation: {p['elevation_m']}")
        print(f"    floor_level: {p['floor_level_m']}")

        readings = build_property_hydrograph(
            mapped_readings,
            peak_wse,
            travel_time,
            retention,
            p['elevation_m'],
            p['floor_level_m'],
        )

        max_depth = max((r['depth_m'] for r in readings), default=0)
        max_wse = max((r['wse_m'] for r in readings), default=0)
        flooded_hours = sum(1 for r in readings if r['flooded'])

        print(f"    -> max_wse: {max_wse:.3f}")
        print(f"    -> max_depth: {max_depth:.3f}")
        print(f"    -> flooded_hours: {flooded_hours}")

        # Show first few readings around the peak
        peak_idx = next((i for i, r in enumerate(readings) if r['depth_m'] == max_depth), 0)
        start = max(0, peak_idx - 2)
        end = min(len(readings), peak_idx + 3)
        print(f"    Readings around peak (hours {start}-{end}):")
        for r in readings[start:end]:
            print(f"      hr={r['hour']}, wse={r['wse_m']:.3f}, "
                  f"depth={r['depth_m']:.3f}, flooded={r['flooded']}")

        assert max_depth > 0, (
            f"build_property_hydrograph returned zero depth despite "
            f"peak_wse={peak_wse:.3f} > flood_threshold={p['elevation_m'] + p['floor_level_m']:.2f}"
        )


# -----------------------------------------------------------------------
# 4. Portfolio statistics
# -----------------------------------------------------------------------

class TestPortfolioFloodStats:
    """Overall portfolio flood statistics."""

    def test_flood_portfolio_summary(self, properties, gaugets):
        """Print summary stats for the flood portfolio."""
        total_props = len(properties)
        props_with_floods = 0
        total_events = 0
        total_flooded = 0

        for pid, p in properties.items():
            events = p.get('flood_events', [])
            total_events += len(events)
            flooded = sum(1 for e in events if e.get('flooded', False))
            total_flooded += flooded
            if flooded > 0:
                props_with_floods += 1

        print(f"\n  === FLOOD PORTFOLIO SUMMARY ===")
        print(f"  Properties: {total_props}")
        print(f"  Properties with floods: {props_with_floods} ({props_with_floods/total_props*100:.1f}%)")
        print(f"  Total flood events: {total_events}")
        print(f"  Events that flood property: {total_flooded} ({total_flooded/total_events*100:.2f}%)" if total_events else "  No events")

        # Show top 5 most-flooded properties
        flood_counts = sorted(
            [(pid, sum(1 for e in p.get('flood_events', []) if e.get('flooded', False)))
             for pid, p in properties.items()],
            key=lambda x: x[1], reverse=True
        )[:5]
        print(f"\n  Top 5 most-flooded properties:")
        for pid, count in flood_counts:
            p = properties[pid]
            print(f"    {pid}: {count} floods, elev={p['elevation_m']}m, "
                  f"floor={p['floor_level_m']}m, zone={p.get('flood_zone', '?')}")

    def test_gauge_storm_count_vs_property_event_count(self, properties, gaugets):
        """Verify properties receive the expected number of storm events."""
        for pid, p in list(properties.items())[:5]:
            ng_list = p.get('nearest_gauges', [])
            if not ng_list:
                continue

            # Count unique alert storms across nearest gauges
            unique_storms = set()
            for ng in ng_list:
                gid = ng['gauge_id']
                gt = gaugets.get(gid, {})
                sr = gt.get('storm_responses', {})
                responses = sr.get('responses', []) if isinstance(sr, dict) else sr
                for r in responses:
                    if r.get('exceeded_alert', False):
                        unique_storms.add(r.get('storm_id', ''))

            n_events = len(p.get('flood_events', []))
            print(f"\n  {pid}: alert storms at gauges={len(unique_storms)}, "
                  f"flood_events in file={n_events}")
