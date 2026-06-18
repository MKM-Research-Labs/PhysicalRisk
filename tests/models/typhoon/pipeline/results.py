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

"""Tests for models.typhoon.pipeline.results — output dataclasses."""

import pytest

from models.typhoon.pipeline.results import (
    PropertyPeakWindSummary,
    TyphoonEventEnsemble,
)


def _summary(**overrides):
    defaults = dict(
        property_id="P1",
        longitude=5.0,
        latitude=5.0,
        n_realizations=4,
        peak_sustained_samples=[10.0, 20.0, 30.0, 40.0],
        peak_sustained_mean=25.0,
        peak_sustained_p50=25.0,
        peak_sustained_p95=38.5,
        peak_sustained_p99=39.7,
        threshold_exceedance={17.5: 0.75, 30.0: 0.5},
        mean_duration_above_ms={17.5: 2.0, 30.0: 1.0},
    )
    defaults.update(overrides)
    return PropertyPeakWindSummary(**defaults)


class TestPropertyPeakWindSummary:

    def test_roundtrip(self):
        s = _summary()
        s2 = PropertyPeakWindSummary.from_dict(s.to_dict())
        assert s2 == s

    def test_to_dict_encodes_threshold_keys_as_strings(self):
        d = _summary().to_dict()
        for k in d["threshold_exceedance"]:
            assert isinstance(k, str)
        for k in d["mean_duration_above_ms"]:
            assert isinstance(k, str)

    def test_from_dict_recovers_float_threshold_keys(self):
        d = _summary().to_dict()
        s2 = PropertyPeakWindSummary.from_dict(d)
        for k in s2.threshold_exceedance:
            assert isinstance(k, float)


class TestTyphoonEventEnsemble:

    def test_roundtrip(self):
        ens = TyphoonEventEnsemble(
            catchment_id="test",
            n_events=5,
            n_particles=10,
            horizon_hours=72.0,
            dt_hours=1.0,
            properties=[_summary(), _summary(property_id="P2", longitude=6.0)],
            metadata={"elapsed_seconds": 0.5, "use_plausibility": True},
        )
        ens2 = TyphoonEventEnsemble.from_dict(ens.to_dict())
        assert ens2 == ens
        assert ens2.metadata["use_plausibility"] is True

    def test_empty_properties_acceptable(self):
        ens = TyphoonEventEnsemble(
            catchment_id="test", n_events=0, n_particles=10,
            horizon_hours=72.0, dt_hours=1.0, properties=[],
        )
        ens2 = TyphoonEventEnsemble.from_dict(ens.to_dict())
        assert ens2.properties == []
