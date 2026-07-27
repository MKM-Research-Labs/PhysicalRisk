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

import config.frequency._loader as freq_loader
from config.frequency import load_frequency_config
from port.src.property.hc.generator import PropertyHazardCurveGenerator
from port.src.property.hc.pricing._loss import property_loss_block
from port.src.property.hc.pricing._wind import _WindMixin, decoupled_wind_legs

from .conftest import basic_output_dir, write_property_ts  # noqa: F401


class _WindHost(_WindMixin):
    """A bare wind host whose index and sequence map are pre-seeded, so the
    record-building logic is exercised without the typhoon filesystem."""


def _wind_host(damage_ratio=0.4, peak=70.0, threshold=50.0):
    host = _WindHost()
    host._wind_damage_cache = {
        "EVT-00000": {"PROP-1": {
            "peak_sustained_ms": peak, "threshold_ms": threshold,
            "v_50_eff_ms": threshold, "damage_ratio": damage_ratio}}}
    host._seq_to_event_cache = {"S0": "EVT-00000"}
    return host


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


class TestWindLoss:
    """Stage 6e: the wind peril gets its own additive loss block, built by the
    same peril-agnostic loss builder the flood leg uses."""

    def test_wind_union_emits_sequence_space_loss_records(self):
        host = _wind_host(damage_ratio=0.4)
        result = host._wind_union("PROP-1", [], num_storms=100)
        # The wind-triggered event maps back to its sequence and carries the
        # authoritative per-event damage ratio.
        assert result["wind_loss_records"] == [
            {"storm_id": "S0", "damage_ratio": 0.4}]

    def test_a_sub_threshold_asset_has_no_wind_loss_records(self):
        host = _wind_host(peak=20.0, threshold=50.0)  # below onset
        result = host._wind_union("PROP-1", [], num_storms=100)
        assert result["wind_loss_records"] == []

    def test_process_attaches_a_wind_loss_block(self, monkeypatch, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-wind", n_floods=2)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        monkeypatch.setattr(gen, "_wind_union", lambda *a, **k: {
            "wind_count": 1, "union_count": 2, "joint_count": 1,
            "wind_spread_bps": 10.0, "union_spread_bps": 20.0,
            "joint_spread_bps": 5.0,
            "wind_loss_records": [{"storm_id": "S0", "damage_ratio": 0.6}],
        })
        result = gen._process_property(
            pdata, gauge_hazard, None, num_storms=100,
            frame=_frame(), lambda_per_year=4.5,
            freq_config=load_frequency_config("thames"), catchment="thames",
            value_lookup={"PROP-wind": 300_000.0})

        wind = result["loss_metrics_wind"]
        assert wind["basis"] == "currency"
        assert wind["exposure_value"] == 300_000.0
        assert wind["reconciliation"]["within_tolerance"]
        # The flood block is still there and independent of the wind one.
        assert "loss_metrics" in result

    def test_a_distinct_wind_lambda_prices_the_wind_block_on_its_own_rate(
            self, monkeypatch, basic_output_dir):
        """Stage 6f: the wind block is priced on the wind arrival rate and its
        own matching draws, so a distinct wind lambda flows through and still
        reconciles."""
        from models.frequency import shared_draws

        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-wl", n_floods=2)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        monkeypatch.setattr(gen, "_wind_union", lambda *a, **k: {
            "wind_count": 1, "union_count": 2, "joint_count": 1,
            "wind_spread_bps": 10.0, "union_spread_bps": 20.0,
            "joint_spread_bps": 5.0,
            "wind_loss_records": [{"storm_id": "S0", "damage_ratio": 0.5}],
        })
        frame = _frame()
        cfg = load_frequency_config("thames")
        wind_lambda = 9.0  # deliberately distinct from the flood rate of 4.5
        wind_draws = shared_draws(frame, wind_lambda, cfg.simulation)

        result = gen._process_property(
            pdata, gauge_hazard, None, num_storms=100,
            frame=frame, lambda_per_year=4.5, freq_config=cfg, catchment="thames",
            value_lookup={"PROP-wl": 100_000.0},
            wind_lambda_per_year=wind_lambda, wind_loss_draws=wind_draws)

        wind = result["loss_metrics_wind"]
        assert wind["metadata"]["lambda_effective"] == pytest.approx(
            wind_lambda * frame.coverage)
        assert wind["reconciliation"]["within_tolerance"]


class TestDecoupledWind:
    """Stage 6i (opt-in): wind priced as an independent arrival process that
    counts the unpaired typhoons the coupled model drops."""

    @staticmethod
    def _host_with_unpaired():
        host = _WindHost()
        host._wind_damage_cache = {
            "EVT-00000": {"PROP-1": {"peak_sustained_ms": 70, "threshold_ms": 50,
                                     "v_50_eff_ms": 50, "damage_ratio": 0.4}},
            "EVT-00002": {"PROP-1": {"peak_sustained_ms": 70, "threshold_ms": 50,
                                     "v_50_eff_ms": 50, "damage_ratio": 0.5}},
            "EVT-UNPAIRED": {"PROP-1": {"peak_sustained_ms": 80, "threshold_ms": 50,
                                        "v_50_eff_ms": 50, "damage_ratio": 0.6}},
        }
        host._seq_to_event_cache = {"S0": "EVT-00000", "S2": "EVT-00002"}
        return host

    _FLOODS = [{"flooded": True, "exceeded_severe": True, "storm_id": "S0"}]

    def test_legs_count_unpaired_and_keep_inclusion_exclusion(self):
        legs = decoupled_wind_legs(
            wind_eids={"EVT-00000", "EVT-00002", "EVT-UNPAIRED"},
            n_wind_events=3, flood_seqs={"S0"}, paired_wind_seqs={"S0", "S2"},
            frame=_frame(), lambda_flood=4.5, lambda_wind=4.5)
        assert legs["wind_count"] == 3            # the unpaired typhoon is counted
        assert legs["joint_count"] == 1           # only S0 is flood AND (paired) wind
        assert legs["union_count"] == 1 + 3 - 1   # flood + wind - joint
        # Independence: the union is at least the wind leg, the joint at most it.
        assert legs["union_spread_bps"] >= legs["wind_spread_bps"]
        assert legs["joint_spread_bps"] <= legs["wind_spread_bps"]

    def test_coupled_by_default_drops_the_unpaired_typhoon(self):
        res = self._host_with_unpaired()._wind_union(
            "PROP-1", self._FLOODS, 100, frame=_frame(), lambda_per_year=4.5,
            catchment="thames")
        assert res["wind_count"] == 2  # paired S0, S2 only — EVT-UNPAIRED dropped

    def test_opting_in_counts_the_unpaired_typhoon(self, monkeypatch):
        monkeypatch.setattr(
            freq_loader, "DECOUPLED_WIND_CATCHMENTS", frozenset({"thames"}))
        res = self._host_with_unpaired()._wind_union(
            "PROP-1", self._FLOODS, 100, frame=_frame(), lambda_per_year=4.5,
            catchment="thames", wind_lambda_per_year=4.5)
        assert res["wind_count"] == 3
        assert res["joint_count"] == 1
        assert res["union_count"] == 3
        # The additive wind-loss records stay sequence-space (paired only).
        assert len(res["wind_loss_records"]) == 2


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
