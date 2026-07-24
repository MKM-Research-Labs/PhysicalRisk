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

"""Tests for persisting fitted rates (MKM-EF-001).

Two things matter here beyond the mechanics.

**The round trip must be exact.** A provenance record that silently loses its
class or its config hash on the way to storage is worse than no provenance:
it looks like evidence and is not.

**The provenance class cannot be defaulted.** On a synthetic catchment the
gauge record is generated *from* an assumed flood frequency, so a rate
extracted from it recovers the generator's own input. Letting a caller omit
the class and get ``observed`` would launder an assumption into evidence.
"""

from datetime import datetime, timedelta

import pytest

from config.frequency import load_frequency_config
from models.frequency import (
    ProvenanceClass,
    calibrate_gauge_rate,
    rate_from_dict,
    rate_to_dict,
)

_START = datetime(2000, 1, 1)


def _record(n_days=3650, flood_every=80):
    return [
        {"date": (_START + timedelta(days=i)).strftime("%Y-%m-%d"),
         "level_meters": 5.0 if i % flood_every == 0 else 1.0}
        for i in range(n_days)
    ]


def _rate(**kwargs):
    settings = {
        "provenance_class": ProvenanceClass.GENERATOR_DERIVED,
        "source_dataset": "gauge_historical_daily",
        "fitted_at": "2026-07-24T00:00:00+00:00",
    }
    settings.update(kwargs)
    return calibrate_gauge_rate(
        "GAUGE-1", _record(), "level_meters", load_frequency_config(), **settings)


class TestRoundTrip:

    def test_a_rate_survives_serialisation_exactly(self):
        rate = _rate()
        assert rate_from_dict(rate_to_dict(rate)) == rate

    def test_the_provenance_class_survives_as_an_enum(self):
        """Not as the bare string it is stored as."""
        rate = _rate(provenance_class=ProvenanceClass.REGIONAL_FALLBACK)
        restored = rate_from_dict(rate_to_dict(rate))
        assert restored.provenance.provenance_class is ProvenanceClass.REGIONAL_FALLBACK

    def test_every_provenance_field_is_carried(self):
        rate = _rate()
        stored = rate_to_dict(rate)["provenance"]
        for field in ("provenance_class", "source_dataset", "record_start",
                      "record_end", "value_key", "declustering_window_days",
                      "config_hash", "model_id", "model_version", "fitted_at"):
            assert field in stored, field

    def test_the_document_is_json_serialisable(self):
        import json

        json.dumps(rate_to_dict(_rate()))

    def test_a_partial_record_fails_rather_than_defaulting(self):
        """Provenance that cannot be read back in full is not provenance."""
        payload = rate_to_dict(_rate())
        del payload["provenance"]["config_hash"]
        with pytest.raises(KeyError):
            rate_from_dict(payload)


class TestCalibrationDocument:

    def test_the_provenance_class_is_required(self):
        """No default — a synthetic record must not be recorded as observed."""
        from models.frequency import calibrate_catchment

        with pytest.raises(TypeError):
            calibrate_catchment("halong")

    def test_the_metadata_records_what_produced_it(self):
        from config.frequency import MODEL_ID, config_hash

        settings = load_frequency_config()
        rate = _rate()
        # The document metadata mirrors these; assert the pieces exist to build it.
        assert rate.provenance.model_id == MODEL_ID
        assert rate.provenance.config_hash == config_hash(settings)


class TestTheValidationArmIsCircular:
    """The per-gauge extraction cannot validate the catchment rate it was
    configured from.

    ``load_frequency_config`` sets the peaks-over-threshold search target from
    the catchment lambda, so the search picks whatever threshold delivers that
    rate and the recovered lambda equals the seed by construction. Measured on
    halong: all four gauges returned 4.48-4.58 against a seed of 4.5.

    This is a second circularity on top of the one in the plan's §5, and it
    means the arm validates the *extraction code*, not the rate. Pinned here so
    the property is explicit rather than discovered again later.
    """

    def test_the_recovered_rate_tracks_the_configured_target(self):
        from config.frequency import PotConfig

        for target in (2.0, 4.5, 8.0):
            settings = load_frequency_config(
                pot=PotConfig(target_exceedance_rate_per_year=target))
            rate = calibrate_gauge_rate(
                "GAUGE-1", _record(n_days=7300, flood_every=40), "level_meters",
                settings, ProvenanceClass.GENERATOR_DERIVED, "test",
                fitted_at="2026-07-24T00:00:00+00:00")
            if rate.diagnostics.threshold_converged:
                assert rate.lambda_per_year == pytest.approx(
                    target, abs=settings.pot.target_rate_tolerance), (
                    "the search recovers its own target — it is not a "
                    "measurement of the arrival rate")

    def test_the_dispersion_index_is_still_informative(self):
        """What the arm *can* say: whether arrivals look Poisson. Halong's
        gauges came back at 0.46-0.97, i.e. under-dispersed."""
        rate = _rate()
        assert rate.diagnostics.dispersion_index >= 0.0
        assert len(rate.diagnostics.annual_counts) > 1


class TestSeamRoundTrip:
    """Calibration reaches storage through the ``database`` seam only.

    ``persist.py`` names no file path (rule R6), so these exercise it against
    an isolated catchment rather than the real data directory.
    """

    def test_a_catchment_with_no_gauges_yields_an_empty_document(self, tmp_path):
        from db_helpers import tmp_catchment

        from models.frequency import calibrate_catchment

        with tmp_catchment(tmp_path):
            doc = calibrate_catchment("test", ProvenanceClass.GENERATOR_DERIVED)
        assert doc["rates"] == {}
        assert doc["metadata"]["num_gauges"] == 0

    def test_a_calibrated_catchment_round_trips_through_the_seam(self, tmp_path):
        import database
        from db_helpers import tmp_catchment

        from models.frequency import calibrate_and_save

        with tmp_catchment(tmp_path):
            database.save_gauge_history("test", "GAUGE-1", {
                "daily_observations": _record(),
            })
            written = calibrate_and_save("test", ProvenanceClass.GENERATOR_DERIVED)
            read_back = database.get_frequency_rates("test")

        assert read_back == written
        assert "GAUGE-1" in read_back["rates"]
        restored = rate_from_dict(read_back["rates"]["GAUGE-1"])
        assert restored.gauge_id == "GAUGE-1"
        assert restored.provenance.provenance_class is ProvenanceClass.GENERATOR_DERIVED

    def test_an_unreadable_gauge_is_skipped_not_fatal(self, tmp_path):
        import database
        from db_helpers import tmp_catchment

        from models.frequency import calibrate_catchment

        with tmp_catchment(tmp_path):
            database.save_gauge_history("test", "GAUGE-OK", {
                "daily_observations": _record(),
            })
            database.save_gauge_history("test", "GAUGE-EMPTY", {})
            doc = calibrate_catchment("test", ProvenanceClass.GENERATOR_DERIVED)

        assert "GAUGE-OK" in doc["rates"]
        assert "GAUGE-EMPTY" in doc["metadata"]["skipped_gauges"]
        assert doc["metadata"]["num_skipped"] == 1
