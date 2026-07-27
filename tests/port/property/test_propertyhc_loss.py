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
    assert block["exposure_value"] == 1.0
    assert block["metadata"]["subject_id"] == "PROP-1"
    assert block["reconciliation"]["within_tolerance"]
    assert set(block["aep"]) == {"2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr"}


def test_a_value_makes_the_loss_a_currency_amount():
    """Stage 6d: with an asset value the loss is value x damage_ratio and the
    basis flips to currency, scaling the whole distribution linearly."""
    frame = _frame()
    floods = [{"storm_id": "S0", "damage_ratio": 0.5}]
    cfg = load_frequency_config("thames")

    unit = property_loss_block(frame, floods, 4.5, cfg, "PROP-1", "thames")
    money = property_loss_block(
        frame, floods, 4.5, cfg, "PROP-1", "thames", asset_value=400_000.0)

    assert money["basis"] == "currency"
    assert money["exposure_value"] == 400_000.0
    assert money["metadata"]["average_annual_loss"] == pytest.approx(
        unit["metadata"]["average_annual_loss"] * 400_000.0, rel=1e-6)


def test_a_missing_value_is_zero_currency_not_unit_exposure():
    """A value of zero keeps the currency basis and reports a zero loss, so a
    portfolio data gap does not silently rebase one asset to a severity."""
    frame = _frame()
    floods = [{"storm_id": "S0", "damage_ratio": 0.5}]
    block = property_loss_block(
        frame, floods, 4.5, load_frequency_config("thames"), "PROP-1", "thames",
        asset_value=0.0)
    assert block["basis"] == "currency"
    assert block["exposure_value"] == 0.0
    assert block["metadata"]["average_annual_loss"] == 0.0


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

    def test_a_value_lookup_makes_the_block_monetary(self, basic_output_dir):
        """Stage 6d: the generator path passes a value lookup, so the asset's
        block is priced in currency at its own value."""
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-money", n_floods=3)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(
            pdata, gauge_hazard, None, num_storms=100,
            frame=_frame(), lambda_per_year=4.5,
            freq_config=load_frequency_config("thames"), catchment="thames",
            value_lookup={"PROP-money": 250_000.0})

        block = result["loss_metrics"]
        assert block["basis"] == "currency"
        assert block["exposure_value"] == 250_000.0
        assert block["reconciliation"]["within_tolerance"]

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


class TestValueLookup:

    def test_it_reads_each_assets_valuation(self, monkeypatch, basic_output_dir):
        import database
        output_dir, _ = basic_output_dir
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        monkeypatch.setattr(database, "list_properties", lambda c: [
            {"PropertyHeader": {"Header": {"PropertyID": "PROP-A"},
                                "Valuation": {"PropertyValue": 500_000}}},
            {"PropertyHeader": {"Header": {"PropertyID": "PROP-B"}}},  # no value -> 0
            {"PropertyHeader": {}},  # no id -> skipped
        ])
        assert gen._load_asset_values("thames") == {
            "PROP-A": 500_000.0, "PROP-B": 0.0}

    def test_an_unreadable_portfolio_yields_an_empty_lookup(
            self, monkeypatch, basic_output_dir):
        import database

        def boom(_catchment):
            raise OSError("portfolio gone")

        output_dir, _ = basic_output_dir
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        monkeypatch.setattr(database, "list_properties", boom)
        assert gen._load_asset_values("thames") == {}
