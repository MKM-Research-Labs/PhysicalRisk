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

"""Round-trip validation of peaks-over-threshold extraction (MKM-EF-001).

On synthetic catchments the gauge daily record is generated *from* an assumed
flood frequency, so extracting a rate from it recovers the generator's own
input. That circularity is documented in
``docs/storm_freq/frequency_layer_definition_and_plan_v2.md`` §5 and it means
these tests validate the *extraction code*, not the frequency of anything.

They are still worth having, and they are the strongest test available at this
stage: if the extractor could not recover a rate it was handed, it would not
recover one from a real record either.

Recovery is deliberately asserted with a wide tolerance. The generator layers
severe-flood injection on top of a seasonal signal, an AR(1) noise process, a
separate minor-flood injection and a placed historical high, all of which can
independently carry the level above a threshold. The recovered rate is
therefore the injected rate *plus* naturally occurring exceedances, and runs
consistently above it.
"""

import pytest

from config.frequency import SOURCE_DATASET_GAUGE_DAILY, load_frequency_config
from models.frequency import ProvenanceClass, calibrate_gauge_rate
from models.frequency.pot import decluster, record_span_years, to_peaks
from models.statistics.synthetic import generate_synthetic_timeseries

_SEVERE = 5.0
_STAMP = "2026-07-22T00:00:00+00:00"


def _gauge(freq_exceed_level3):
    """A minimal gauge record carrying the generator's frequency input."""
    return {
        "FloodGauge": {
            "FloodStages": {
                "FloodAlert": 3.0,
                "FloodWarning": 4.0,
                "SevereFloodWarning": _SEVERE,
            },
            "SensorStats": {
                "HistoricalHighLevel": 6.0,
                "FrequencyExceedLevel3": freq_exceed_level3,
            },
        }
    }


def _severe_event_rate(observations, window_days):
    """The declustered rate of severe exceedances in a generated record."""
    series = to_peaks(observations, "level_meters")
    peaks = decluster([o for o in series if o.value >= _SEVERE], window_days)
    return len(peaks) / record_span_years(series)


def _calibrate(observations):
    return calibrate_gauge_rate(
        "GAUGE-RT", observations, "level_meters", load_frequency_config(),
        ProvenanceClass.GENERATOR_DERIVED, SOURCE_DATASET_GAUGE_DAILY,
        fitted_at=_STAMP)


@pytest.mark.parametrize("years,freq_exceed", [(30, 24), (40, 80)])
def test_extraction_recovers_the_injected_rate_to_within_a_factor(years, freq_exceed):
    """The extracted severe-event rate tracks the injected one, running above
    it because the generator's other components also cross the threshold."""
    observations = generate_synthetic_timeseries(_gauge(freq_exceed), years=years, seed=7)
    injected = freq_exceed / years
    recovered = _severe_event_rate(
        observations, load_frequency_config().pot.declustering_window_days)

    assert recovered >= injected
    assert recovered < injected * 2.0


def test_declustering_materially_reduces_the_day_count():
    """The correction the model exists to make, measured on real generated data:
    counting exceedance-days overstates the event rate."""
    observations = generate_synthetic_timeseries(_gauge(24), years=30, seed=7)
    window = load_frequency_config().pot.declustering_window_days

    series = to_peaks(observations, "level_meters")
    exceedance_days = sum(1 for o in series if o.value >= _SEVERE)
    events = len(decluster([o for o in series if o.value >= _SEVERE], window))

    assert events < exceedance_days


def test_a_higher_injected_frequency_yields_a_higher_extracted_rate():
    """Monotonicity: the extractor must order two gauges the way the generator
    ordered them."""
    quiet = generate_synthetic_timeseries(_gauge(12), years=40, seed=11)
    busy = generate_synthetic_timeseries(_gauge(120), years=40, seed=11)
    window = load_frequency_config().pot.declustering_window_days

    assert _severe_event_rate(busy, window) > _severe_event_rate(quiet, window)


def test_generated_record_calibrates_without_falling_back():
    """A thirty-year generated record is long and busy enough to support its own
    rate, so the fallback must not engage."""
    rate = _calibrate(generate_synthetic_timeseries(_gauge(24), years=30, seed=7))

    assert rate.provenance.provenance_class is ProvenanceClass.GENERATOR_DERIVED
    assert rate.provenance.note == ""
    assert rate.record_years == pytest.approx(30.0, abs=0.1)
    assert rate.diagnostics.threshold_converged


def test_provenance_class_is_not_observed_for_generated_data():
    """The guard against the §5 failure mode: a rate extracted from a synthetic
    record must never be recorded as observed."""
    rate = _calibrate(generate_synthetic_timeseries(_gauge(24), years=30, seed=7))
    assert rate.provenance.provenance_class is not ProvenanceClass.OBSERVED
