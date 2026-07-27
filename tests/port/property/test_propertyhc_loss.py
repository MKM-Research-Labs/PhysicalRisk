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

"""Tests for the property/commercial loss block (MKM-EF-001, Stage 6c).

The loss-weighted view is *additive*: it rides beside the PRS spread without
touching it. Three things are pinned:

- **It appears only on the real generator path.** The block is emitted when the
  frequency layer is active and its config supplied; a caller that passes a
  frame but no config — every pre-existing unit test — gets byte-identical
  output, so the wiring cannot silently perturb the spread.
- **It reconciles.** The per-asset average annual loss matches the closed form,
  the same self-test the sampler carries.
- **It respects the occurrence rule.** Two floods inside one hours-clause event
  contribute one loss, valued at the worse of the two.
"""

import numpy as np
import pytest

from config.frequency import load_frequency_config
from port.src.property.hc.generator import PropertyHazardCurveGenerator
from port.src.property.hc.pricing._loss import property_loss_block

from .conftest import basic_output_dir, write_property_ts  # noqa: F401


def _frame(n_events=10, category="severe"):
    from models.frequency import build_event_frame
    from models.hazard.io import load_storms_from_sequences
    return build_event_frame(load_storms_from_sequences({"sequences": [
        {
            "sequence_id": f"S{i}",
            "storms": [{
                "storm_id": f"ST-{i}", "precipitation_mm": 30.0,
                "duration_hours": 12, "intensity_factor": 1.0,
                "intensity_category": category,
            }],
        }
        for i in range(n_events)
    ]}))


# ------------------------------------------------------- property_loss_block

def test_block_is_attributed_and_reconciles():
    frame = _frame()
    floods = [
        {"storm_id": "S0", "damage_ratio": 0.2},
        {"storm_id": "S1", "damage_ratio": 0.5},
    ]
    block = property_loss_block(
        frame, floods, 4.5, load_frequency_config("thames"), "PROP-1", "thames")

    assert block["basis"] == "unit_exposure_damage_ratio"
    assert block["metadata"]["subject_id"] == "PROP-1"
    assert block["reconciliation"]["within_tolerance"]
    assert set(block["aep"]) == {"2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr"}


def test_two_floods_in_one_event_take_the_worse_loss():
    """The occurrence rule: one event, one loss, at its worst moment."""
    frame = _frame()
    floods = [
        {"storm_id": "S0", "damage_ratio": 0.2},
        {"storm_id": "S0", "damage_ratio": 0.7},
    ]
    block = property_loss_block(
        frame, floods, 4.5, load_frequency_config("thames"), "PROP-1", "thames")
    # AAL = lambda * coverage * weighted mean loss; only event S0 carries 0.7.
    weights = np.asarray(frame.weights)
    lam_eff = 4.5 * frame.coverage
    expected = lam_eff * weights[0] * 0.7
    assert block["metadata"]["average_annual_loss"] == pytest.approx(expected, rel=0.05)


def test_an_asset_with_no_severe_floods_has_zero_loss():
    block = property_loss_block(
        _frame(), [], 4.5, load_frequency_config("thames"), "PROP-0", "thames")
    assert block["metadata"]["average_annual_loss"] == 0.0


# ---------------------------------------------------- gating in _process_property

class TestGating:

    def test_the_block_appears_with_a_config(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-loss", n_floods=3)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(
            pdata, gauge_hazard, None, num_storms=100,
            frame=_frame(), lambda_per_year=4.5,
            freq_config=load_frequency_config("thames"), catchment="thames")

        assert "loss_metrics" in result
        assert result["loss_metrics"]["reconciliation"]["within_tolerance"]
        # The spread is untouched by the loss block.
        assert result["term_structure"]["severe"]["prs_spread_bps"][0] > 0

    def test_no_block_without_a_config(self, basic_output_dir):
        """A frame but no config — the shape every existing unit test uses —
        must not grow a loss block."""
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-nolossconfig", n_floods=3)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(
            pdata, gauge_hazard, None, num_storms=100,
            frame=_frame(), lambda_per_year=4.5)

        assert "loss_metrics" not in result
