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

"""Tests for frequency calibration orchestration (MKM-EF-001).

Covers rate estimation, the regional-fallback rule for thin records,
diagnostics, and the provenance record.

Two properties matter beyond mechanics:

- **Determinism.** Calibration must be a pure function of (observations,
  config) once the timestamp is pinned, so a persisted rate can be reproduced.
- **Decomposition.** lambda x P(exceed | event) must equal the directly
  measured rate of exceedances of that level. This is the identity the Stage 3
  annualisation seam will rely on.
"""

from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from config.frequency import (
    MODEL_ID,
    MODEL_VERSION,
    PERIL_FLOOD,
    PotConfig,
    RateConfig,
    config_hash,
    load_frequency_config,
)
from models.frequency import (
    ProvenanceClass,
    calibrate_gauge_rate,
    fallback_reason,
    summarise,
)
from models.frequency.datastructures import PotExtraction
from models.frequency.pot import decluster, record_span_years, to_peaks

_START = datetime(2000, 1, 1)
_STAMP = "2026-07-22T00:00:00+00:00"
_DATASET = "gauge_historical_daily"


def _day(offset: int) -> str:
    return (_START + timedelta(days=offset)).strftime("%Y-%m-%d")


def _record(n_days, flood_every, flood_value=5.0, base=1.0):
    """A daily record with a one-day flood every *flood_every* days."""
    return [
        {"date": _day(day),
         "level_meters": flood_value if day % flood_every == 0 else base}
        for day in range(n_days)
    ]


def _calibrate(observations, config=None, **kwargs):
    """Calibrate with the fixed timestamp and dataset the tests use."""
    settings = {
        "provenance_class": ProvenanceClass.OBSERVED,
        "source_dataset": _DATASET,
        "fitted_at": _STAMP,
    }
    settings.update(kwargs)
    return calibrate_gauge_rate(
        "GAUGE-1", observations, "level_meters",
        config or load_frequency_config(), **settings)


# ------------------------------------------------------------ rate estimation

def test_rate_is_events_per_year_not_exceedance_days():
    """The whole point of the model, as an arithmetic contrast.

    Ten years with a three-day flood every 180 days holds 21 floods spanning 63
    days above the threshold. The rate is 21 events over the record, not 63 —
    counting days, as the platform does today, overstates it threefold."""
    observations = []
    for day in range(3650):
        in_flood = day % 180 in (0, 1, 2)
        observations.append(
            {"date": _day(day), "level_meters": 5.0 if in_flood else 1.0})

    rate = _calibrate(observations)
    exceedance_days = sum(1 for o in observations if o["level_meters"] >= 5.0)

    assert rate.n_events == 21
    assert exceedance_days == 63
    assert rate.lambda_per_year == pytest.approx(21 / rate.record_years, rel=1e-9)
    assert rate.lambda_per_year == pytest.approx(2.1, abs=0.05)
    # The day-count the existing statistics module would report, for contrast.
    assert exceedance_days / rate.record_years == pytest.approx(6.3, abs=0.05)


def test_rate_reconciles_with_the_declustered_peak_count():
    rate = _calibrate(_record(3650, flood_every=180))
    assert rate.lambda_per_year == pytest.approx(
        rate.n_events / rate.record_years, rel=1e-9)


def test_lambda_times_conditional_equals_the_direct_rate():
    """The decomposition the annualisation seam depends on. Splitting a record
    into events and a conditional must not change the implied rate of severe
    exceedances."""
    severe = 6.0
    observations = []
    flood_index = 0
    for day in range(7300):
        if day % 90 == 0:
            observations.append(
                {"date": _day(day),
                 "level_meters": severe if flood_index % 3 == 0 else 4.0})
            flood_index += 1
        else:
            observations.append({"date": _day(day), "level_meters": 1.0})

    rate = _calibrate(observations)
    series = to_peaks(observations, "level_meters")
    window = load_frequency_config().pot.declustering_window_days

    event_peaks = decluster([o for o in series if o.value >= rate.threshold], window)
    conditional = sum(1 for p in event_peaks if p.value >= severe) / len(event_peaks)
    direct_rate = (len(decluster([o for o in series if o.value >= severe], window))
                   / record_span_years(series))

    assert rate.lambda_per_year * conditional == pytest.approx(direct_rate, rel=1e-9)


# --------------------------------------------------------------- fallback rule

def test_short_record_falls_back_to_the_regional_rate():
    config = load_frequency_config()
    rate = _calibrate(_record(365, flood_every=60), config)
    assert rate.lambda_per_year == config.rate.regional_fallback_lambda_per_year
    assert rate.provenance.provenance_class is ProvenanceClass.REGIONAL_FALLBACK
    assert "shorter than" in rate.provenance.note


def test_sparse_record_falls_back_to_the_regional_rate():
    """Long enough, but only two floods in it."""
    config = load_frequency_config()
    observations = [
        {"date": _day(day), "level_meters": 5.0 if day in (10, 2000) else 1.0}
        for day in range(3650)
    ]
    rate = _calibrate(observations, config)
    assert rate.lambda_per_year == config.rate.regional_fallback_lambda_per_year
    assert rate.provenance.provenance_class is ProvenanceClass.REGIONAL_FALLBACK
    assert "fewer than" in rate.provenance.note


def test_fallback_overrides_the_caller_supplied_provenance_class():
    """A fallback rate is not observed data, whatever the caller passed."""
    rate = _calibrate(_record(365, flood_every=60),
                      provenance_class=ProvenanceClass.OBSERVED)
    assert rate.provenance.provenance_class is ProvenanceClass.REGIONAL_FALLBACK


def test_adequate_record_keeps_the_caller_supplied_provenance_class():
    rate = _calibrate(_record(3650, flood_every=180),
                      provenance_class=ProvenanceClass.GENERATOR_DERIVED)
    assert rate.provenance.provenance_class is ProvenanceClass.GENERATOR_DERIVED
    assert rate.provenance.note == ""


def test_fallback_reason_is_empty_for_an_adequate_record():
    extraction = PotExtraction(
        threshold=1.0, peaks=(), annual_counts=(), record_start="", record_end="",
        record_years=10.0, achieved_rate_per_year=0.0, threshold_converged=True)
    config = load_frequency_config(rate=RateConfig(min_events_for_rate=0))
    assert fallback_reason(extraction, config) == ""


def test_empty_record_falls_back_rather_than_raising():
    rate = _calibrate([])
    assert rate.provenance.provenance_class is ProvenanceClass.REGIONAL_FALLBACK
    assert rate.n_events == 0
    assert rate.record_years == 0.0


# ----------------------------------------------------------------- diagnostics

def test_dispersion_index_of_a_regular_series_is_near_zero():
    """A flood exactly every 180 days gives an almost constant annual count, so
    the variance — and the dispersion index — is far below Poisson's one."""
    rate = _calibrate(_record(3650 * 2, flood_every=180))
    assert rate.diagnostics.dispersion_index < 1.0


def test_diagnostics_are_zero_when_there_are_no_counts():
    extraction = PotExtraction(
        threshold=0.0, peaks=(), annual_counts=(), record_start="", record_end="",
        record_years=0.0, achieved_rate_per_year=0.0, threshold_converged=False)
    diagnostics = summarise(extraction)
    assert diagnostics.mean_count == 0.0
    assert diagnostics.variance_count == 0.0
    assert diagnostics.dispersion_index == 0.0


def test_variance_is_zero_for_a_single_year_block():
    extraction = PotExtraction(
        threshold=0.0, peaks=(), annual_counts=(3,), record_start="", record_end="",
        record_years=1.0, achieved_rate_per_year=3.0, threshold_converged=True)
    diagnostics = summarise(extraction)
    assert diagnostics.variance_count == 0.0
    assert diagnostics.dispersion_index == 0.0
    assert diagnostics.mean_count == 3.0


def test_dispersion_index_is_variance_over_mean():
    extraction = PotExtraction(
        threshold=0.0, peaks=(), annual_counts=(0, 2, 4), record_start="",
        record_end="", record_years=3.0, achieved_rate_per_year=2.0,
        threshold_converged=True)
    diagnostics = summarise(extraction)
    assert diagnostics.mean_count == pytest.approx(2.0)
    assert diagnostics.variance_count == pytest.approx(4.0)
    assert diagnostics.dispersion_index == pytest.approx(2.0)


def test_diagnostics_carry_the_extraction_convergence_flag():
    # A flood every 80 days is about 4.5 a year, matching the seeded Thames
    # arrival rate the threshold search targets.
    rate = _calibrate(_record(3650, flood_every=80))
    assert rate.diagnostics.threshold_converged is True
    assert rate.diagnostics.achieved_rate_per_year == pytest.approx(
        rate.lambda_per_year, rel=1e-9)


# ------------------------------------------------------------------ provenance

def test_provenance_records_the_full_recipe():
    config = load_frequency_config()
    rate = _calibrate(_record(3650, flood_every=180), config)
    provenance = rate.provenance

    assert provenance.source_dataset == _DATASET
    assert provenance.value_key == "level_meters"
    assert provenance.declustering_window_days == config.pot.declustering_window_days
    assert provenance.config_hash == config_hash(config)
    assert provenance.model_id == MODEL_ID
    assert provenance.model_version == MODEL_VERSION
    assert provenance.fitted_at == _STAMP
    assert provenance.record_start == _day(0)
    assert provenance.record_end == _day(3649)


def test_default_peril_is_flood():
    assert _calibrate(_record(3650, flood_every=180)).peril == PERIL_FLOOD


def test_timestamp_defaults_to_now_when_not_supplied():
    rate = calibrate_gauge_rate(
        "GAUGE-1", _record(3650, flood_every=180), "level_meters",
        load_frequency_config(), ProvenanceClass.OBSERVED, _DATASET)
    assert rate.provenance.fitted_at
    assert rate.provenance.fitted_at != _STAMP


def test_annual_rate_accessor_matches_the_field():
    rate = _calibrate(_record(3650, flood_every=180))
    assert rate.annual_rate() == rate.lambda_per_year


# ---------------------------------------------------------------- determinism

def test_calibration_is_deterministic():
    """The golden-master property: same data, same config, same output."""
    observations = _record(3650, flood_every=180)
    first = _calibrate(observations)
    second = _calibrate(observations)
    assert first == second


def test_config_change_changes_the_recorded_hash():
    observations = _record(3650, flood_every=180)
    base = load_frequency_config()
    widened = load_frequency_config(
        pot=replace(base.pot, declustering_window_days=10))

    assert (_calibrate(observations, base).provenance.config_hash
            != _calibrate(observations, widened).provenance.config_hash)


def test_a_wider_declustering_window_never_finds_more_events():
    """Merging clusters can only reduce the event count at a fixed threshold."""
    observations = []
    for day in range(3650):
        in_flood = day % 90 in (0, 2, 4, 6)
        observations.append(
            {"date": _day(day), "level_meters": 5.0 if in_flood else 1.0})

    series = to_peaks(observations, "level_meters")
    exceedances = [o for o in series if o.value >= 5.0]
    narrow = len(decluster(exceedances, 3))
    wide = len(decluster(exceedances, 30))
    assert wide <= narrow


def test_config_hash_is_stable_across_equal_configs():
    assert config_hash(load_frequency_config()) == config_hash(load_frequency_config())


def test_config_hash_length_is_bounded():
    from config.frequency import CONFIG_HASH_CHARS
    assert len(config_hash(load_frequency_config())) == CONFIG_HASH_CHARS


def test_pot_config_overrides_are_honoured():
    config = load_frequency_config(pot=PotConfig(target_exceedance_rate_per_year=5.0))
    assert config.pot.target_exceedance_rate_per_year == 5.0
    assert config.rate.min_record_years == RateConfig().min_record_years
