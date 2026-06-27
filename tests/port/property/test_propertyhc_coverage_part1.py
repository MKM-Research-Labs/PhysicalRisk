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
Coverage-completion tests for property hazard curve modules (part 1):
  - generator.py: skipped property, progress log, decomposition edge cases
  - loader.py: sequence_gauge enrichment
  - pricing.py: synthetic gauge basis and spreads
"""

from unittest.mock import patch

import pytest
from db_helpers import tmp_catchment

import database
from port.src.property.propertyhc import (
    TENORS,
    PropertyHazardCurveGenerator,
)

from .conftest import write_gauge_hc, write_property_ts

_CATCHMENT = "thames"


@pytest.fixture(autouse=True)
def _seam_backend(tmp_path):
    """Bind a scratch backend rooted at tmp_path so the generator's hazard-curve
    reads/writes (now on the database seam) resolve there."""
    with tmp_catchment(tmp_path, _CATCHMENT):
        yield


# ===========================================================================
# generator.py line 126 — properties_skipped incremented
# ===========================================================================

class TestGeneratorSkippedProperty:

    def test_skipped_property_increments_stats(self, basic_output_dir):
        """When _process_property returns None, properties_skipped += 1."""
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-skip1", n_floods=3)

        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)

        original = gen._process_property

        def returns_none(pf, gh, ppf, ns):
            return None

        with patch.object(gen, '_process_property', side_effect=returns_none):
            stats = gen.generate()

        assert stats['properties_skipped'] == 1
        assert stats['properties_processed'] == 0


# ===========================================================================
# generator.py line 129 — progress log every 50 properties
# ===========================================================================

class TestGeneratorProgressLog:

    def test_progress_logged_at_50_properties(self, basic_output_dir, caplog):
        """Progress message appears after processing 50 properties."""
        output_dir, pts_dir = basic_output_dir
        for i in range(51):
            write_property_ts(pts_dir, f"PROP-{i:04d}", n_floods=1)

        import logging
        gen = PropertyHazardCurveGenerator(output_dir, verbose=True)
        logger_name = gen.__class__.__module__
        with caplog.at_level(logging.INFO, logger=logger_name):
            stats = gen.generate()

        assert stats['properties_processed'] == 51
        progress_msgs = [r for r in caplog.records if 'Processed 50/' in r.message]
        assert len(progress_msgs) >= 1


# ===========================================================================
# generator.py lines 177-178 — decomposition when propertyhc.json missing
# ===========================================================================

class TestDecompositionMissingHcFile:

    def test_returns_zero_when_propertyhc_missing(self, tmp_path):
        """attach_spread_decomposition returns 0 when propertyhc.json absent."""
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        result = gen.attach_spread_decomposition()
        assert result == 0


# ===========================================================================
# generator.py lines 213-219 — decomposition idw_gauge_spreads fallback
# ===========================================================================

class TestDecompositionIdwFallback:

    def test_uses_idw_gauge_spreads_when_no_synth(self, tmp_path):
        """When no SYNTH- gauge exists, uses idw_gauge_spreads fallback."""
        hc_data = {
            'metadata': {'catchment_id': 'test', 'tenors': TENORS},
            'property_hazard_curves': {
                'PROP-001': {
                    'nearest_gauges': [
                        {'gauge_id': 'GAUGE-001', 'distance_km': 1.0},
                    ],
                    'idw_gauge_spreads': {
                        'severe': [10.0, 20.0, 30.0, 40.0, 50.0],
                    },
                    'term_structure': {
                        'severe': {'prs_spread_bps': [5.0, 10.0, 15.0, 20.0, 25.0]},
                    },
                },
            },
        }
        database.save_property_hazard_curves(_CATCHMENT, hc_data)

        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        count = gen.attach_spread_decomposition()

        assert count == 1
        result = database.get_property_hazard_curves(_CATCHMENT)
        decomp = result['property_hazard_curves']['PROP-001']['spread_decomposition']
        # gauge_spread should come from idw_gauge_spreads[4] = 50.0
        assert decomp['gauge_spread_bps'] == 50.0

    def test_uses_synth_gauge_basis_when_present(self, tmp_path):
        """When SYNTH- gauge exists in nearest_gauges, uses synth basis for gauge_spread."""
        hc_data = {
            'metadata': {'catchment_id': 'test', 'tenors': TENORS},
            'property_hazard_curves': {
                'PROP-002': {
                    'nearest_gauges': [
                        {
                            'gauge_id': 'SYNTH-001',
                            'distance_km': 0.5,
                            'basis_bps': {
                                'severe': {
                                    'values': [10.0, 10.0, 10.0, 10.0, 10.0],
                                },
                            },
                        },
                    ],
                    'term_structure': {
                        'severe': {'prs_spread_bps': [50.0, 50.0, 50.0, 50.0, 50.0]},
                    },
                },
            },
        }
        database.save_property_hazard_curves(_CATCHMENT, hc_data)

        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        count = gen.attach_spread_decomposition()

        assert count == 1
        result = database.get_property_hazard_curves(_CATCHMENT)
        decomp = result['property_hazard_curves']['PROP-002']['spread_decomposition']
        # gauge_spread = prop_5yr[4] + synth_basis[4] = 50.0 + 10.0 = 60.0
        assert decomp['gauge_spread_bps'] == 60.0


class TestDecompositionBriLeg:
    """The 5th basis step: no-BRI property floor → BRI-adjusted floor."""

    def _base_hc(self):
        return {
            'metadata': {'catchment_id': 'test', 'tenors': TENORS},
            'property_hazard_curves': {
                'PROP-001': {
                    'nearest_gauges': [{'gauge_id': 'GAUGE-001', 'distance_km': 1.0}],
                    'idw_gauge_spreads': {'severe': [10.0, 20.0, 30.0, 40.0, 50.0]},
                    'term_structure': {
                        'severe': {'prs_spread_bps': [5.0, 10.0, 15.0, 20.0, 200.0]},
                    },
                },
            },
        }

    def test_bri_leg_attached_when_curve_present(self, tmp_path):
        """propertyhc.json present → bri_spread_bps + resilience_effect_bps =
        no-BRI 5yr severe spread − BRI 5yr severe spread."""
        database.save_property_hazard_curves(_CATCHMENT, self._base_hc())
        # BRI-adjusted floor raises the threshold → lower severe spread (168 vs 200).
        bri_data = {
            'property_hazard_curves': {
                'PROP-001': {
                    'term_structure': {
                        'severe': {'prs_spread_bps': [4.0, 8.0, 12.0, 16.0, 168.0]},
                    },
                },
            },
        }
        database.save_property_hazard_curves(_CATCHMENT, bri_data, mode='bri')

        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        assert gen.attach_spread_decomposition() == 1
        decomp = database.get_property_hazard_curves(
            _CATCHMENT)['property_hazard_curves']['PROP-001']['spread_decomposition']
        assert decomp['bri_spread_bps'] == 168.0
        assert decomp['resilience_effect_bps'] == pytest.approx(32.0)  # 200 - 168
        assert decomp['resilience_effect_bps'] >= 0  # raising floor only reduces spread

    def test_bri_leg_omitted_when_curve_absent(self, tmp_path):
        """No propertybri.json → decomposition omits the resilience leg
        (safe no-op for pipelines that never ran the bri stage)."""
        database.save_property_hazard_curves(_CATCHMENT, self._base_hc())

        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        assert gen.attach_spread_decomposition() == 1
        decomp = database.get_property_hazard_curves(
            _CATCHMENT)['property_hazard_curves']['PROP-001']['spread_decomposition']
        assert 'bri_spread_bps' not in decomp
        assert 'resilience_effect_bps' not in decomp
