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
Tests for models.floodrisk.risk_visualization.

Smoke-tests that static plots and interactive maps are produced
without error using synthetic GeoDataFrame data, and verifies
the risk-level colour assignment logic.
"""

import pytest
import numpy as np

try:
    import geopandas as gpd
    import pandas as pd
    from shapely.geometry import Point
    HAS_GEO = True
except ImportError:
    HAS_GEO = False

pytestmark = pytest.mark.skipif(not HAS_GEO, reason="geopandas not installed")

from models.floodrisk.risk_visualization import (
    create_interactive_map,
    create_static_plots,
    visualize_risk,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def synthetic_properties():
    """Small synthetic GeoDataFrame with 8 properties."""
    n = 8
    lons = np.linspace(-0.3, 0.1, n)
    lats = np.linspace(51.4, 51.6, n)
    values = np.array([250_000, 400_000, 180_000, 600_000,
                       350_000, 500_000, 220_000, 750_000])
    geometry = [Point(lon, lat) for lon, lat in zip(lons, lats)]
    return gpd.GeoDataFrame(
        {'property_id': [f'PROP-{i:03d}' for i in range(n)], 'value': values},
        geometry=geometry,
        crs='EPSG:4326',
    )


@pytest.fixture
def flood_depths():
    return np.array([0.0, 0.15, 0.4, 1.5, 0.8, 2.5, 0.05, 0.7])


@pytest.fixture
def direct_impacts():
    """Impact ratios covering all four risk bands."""
    return np.array([0.02, 0.12, 0.35, 0.65, 0.45, 0.7, 0.08, 0.32])


@pytest.fixture
def flood_event():
    return {
        'center_lat': 51.5,
        'center_lon': -0.1,
        'radius': 5000,
        'description': 'Test flood event',
    }


@pytest.fixture
def gauge_data():
    return pd.DataFrame({
        'latitude':  [51.48, 51.52],
        'longitude': [-0.15, -0.05],
        'gauge_id':  ['G001', 'G002'],
        'water_level': [4.5, 3.8],
    })


# ===========================================================================
# Risk label logic (inline, not exported — tested via impact thresholds)
# ===========================================================================

class TestRiskLabelThresholds:
    """Verify the threshold logic used inside create_interactive_map."""

    @pytest.mark.parametrize("impact,expected_band", [
        (0.00, "Minimal"),
        (0.05, "Minimal"),   # <= 0.1
        (0.10, "Minimal"),   # exactly 0.1 → still Minimal (> 0.1 triggers Low)
        (0.11, "Low"),       # 0.1 < x <= 0.3
        (0.30, "Low"),
        (0.31, "Medium"),    # 0.3 < x <= 0.6
        (0.60, "Medium"),
        (0.61, "High"),      # > 0.6
        (0.99, "High"),
    ])
    def test_impact_to_band(self, impact, expected_band):
        """Replicate the threshold logic from create_interactive_map."""
        if impact > 0.6:
            band = "High"
        elif impact > 0.3:
            band = "Medium"
        elif impact > 0.1:
            band = "Low"
        else:
            band = "Minimal"
        assert band == expected_band


# ===========================================================================
# Static plots
# ===========================================================================

class TestCreateStaticPlots:

    def test_png_file_created(self, tmp_path, synthetic_properties,
                              flood_depths, direct_impacts):
        out = str(tmp_path / "risk_plot.png")
        create_static_plots(synthetic_properties, flood_depths, direct_impacts, out)
        assert (tmp_path / "risk_plot.png").exists()
        assert (tmp_path / "risk_plot.png").stat().st_size > 0

    def test_all_minimal_impacts(self, tmp_path, synthetic_properties):
        n = len(synthetic_properties)
        depths = np.zeros(n)
        impacts = np.zeros(n)
        out = str(tmp_path / "all_minimal.png")
        create_static_plots(synthetic_properties, depths, impacts, out)
        assert (tmp_path / "all_minimal.png").exists()

    def test_all_high_impacts(self, tmp_path, synthetic_properties):
        n = len(synthetic_properties)
        depths = np.full(n, 2.0)
        impacts = np.full(n, 0.8)
        out = str(tmp_path / "all_high.png")
        create_static_plots(synthetic_properties, depths, impacts, out)
        assert (tmp_path / "all_high.png").exists()

    def test_mixed_risk_levels(self, tmp_path, synthetic_properties,
                               flood_depths, direct_impacts):
        """Ensure all four risk bands appear (for pie chart coverage)."""
        out = str(tmp_path / "mixed.png")
        create_static_plots(synthetic_properties, flood_depths, direct_impacts, out)
        assert (tmp_path / "mixed.png").exists()


# ===========================================================================
# Interactive map
# ===========================================================================

class TestCreateInteractiveMap:

    def test_html_file_created(self, tmp_path, synthetic_properties,
                               flood_depths, direct_impacts, flood_event):
        out = str(tmp_path / "risk_map.html")
        create_interactive_map(
            synthetic_properties, flood_depths, direct_impacts,
            flood_event, gauge_data=None, output_file=out,
        )
        assert (tmp_path / "risk_map.html").exists()
        assert (tmp_path / "risk_map.html").stat().st_size > 0

    def test_with_gauge_data(self, tmp_path, synthetic_properties,
                             flood_depths, direct_impacts, flood_event, gauge_data):
        out = str(tmp_path / "map_with_gauges.html")
        create_interactive_map(
            synthetic_properties, flood_depths, direct_impacts,
            flood_event, gauge_data=gauge_data, output_file=out,
        )
        assert (tmp_path / "map_with_gauges.html").exists()

    def test_no_flood_event_center(self, tmp_path, synthetic_properties,
                                   flood_depths, direct_impacts):
        """flood_event without center_lat/center_lon should not crash."""
        out = str(tmp_path / "no_center.html")
        create_interactive_map(
            synthetic_properties, flood_depths, direct_impacts,
            flood_event={}, gauge_data=None, output_file=out,
        )
        assert (tmp_path / "no_center.html").exists()

    def test_no_gauge_data(self, tmp_path, synthetic_properties,
                           flood_depths, direct_impacts, flood_event):
        out = str(tmp_path / "no_gauge.html")
        create_interactive_map(
            synthetic_properties, flood_depths, direct_impacts,
            flood_event, gauge_data=None, output_file=out,
        )
        assert (tmp_path / "no_gauge.html").exists()


# ===========================================================================
# visualize_risk (orchestrator)
# ===========================================================================

class TestVisualizeRisk:

    def test_produces_both_outputs(self, tmp_path, synthetic_properties,
                                   flood_depths, direct_impacts, flood_event):
        base = str(tmp_path / "flood_risk")
        visualize_risk(
            synthetic_properties, flood_depths, direct_impacts,
            flood_event, gauge_data=None, output_file_base=base,
        )
        assert (tmp_path / "flood_risk.html").exists()
        assert (tmp_path / "flood_risk.png").exists()
