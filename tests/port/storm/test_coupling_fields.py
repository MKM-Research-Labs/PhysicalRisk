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
Stage 2 — storm<->typhoon coupling driver fields.

Verifies that generate_event_set stamps each StormSequence with the three
coupling fields (event_id, base_intensity z, per-event seed), that they
survive serialisation, that they are deterministic for a fixed seed, and —
the key regression guard — that adding the per-event seed stream leaves the
storm draws (and therefore the flood numbers) bit-identical to the
pre-coupling pipeline.

See docs/models/storm_typhoon_coupling/coupling_spec.md (Stage 2).
"""

import numpy as np
import pytest

from config.port import DEFAULT_INTENSITY_WEIGHTS
from port.src.storm_multi.generators.batch_generator import (
    BASE_INTENSITY_PARAMS,
    generate_event_set,
)
from port.src.storm_multi.core.data_structures import StormSequence


@pytest.fixture(scope="module")
def batch():
    return generate_event_set(count=200, catchment_id="thames", seed=42)


class TestCouplingFieldsPresent:

    def test_event_id_sequential_and_unique(self, batch):
        ids = [s.event_id for s in batch]
        assert ids == [f"EVT-{i:05d}" for i in range(len(batch))]
        assert len(set(ids)) == len(ids)

    def test_base_intensity_positive(self, batch):
        # z = max(0.1, Normal(mean_cat, std_cat)) — always strictly positive.
        for s in batch:
            assert s.base_intensity >= 0.1

    def test_seed_present_and_distinct(self, batch):
        seeds = [s.seed for s in batch]
        assert all(isinstance(x, int) for x in seeds)
        # Spawned from SeedSequence — collisions over 200 draws are vanishingly
        # unlikely; require all distinct.
        assert len(set(seeds)) == len(seeds)


class TestSerialisationRoundTrip:

    def test_round_trip_preserves_coupling_fields(self, batch):
        for s in batch[:10]:
            d = s.to_dict()
            assert "event_id" in d and "base_intensity" in d and "seed" in d
            r = StormSequence.from_dict(d)
            assert r.event_id == s.event_id
            assert r.seed == s.seed
            # to_dict rounds z to 6 dp; from_dict must recover that value.
            assert r.base_intensity == pytest.approx(round(s.base_intensity, 6))

    def test_from_dict_defaults_for_pre_coupling_file(self):
        # A pre-Stage-2 sequence dict lacks the coupling keys entirely.
        legacy = {
            "sequence_id": "SEQ-legacy",
            "sequence_type": "isolated",
            "intensity_category": "moderate",
        }
        r = StormSequence.from_dict(legacy)
        assert r.event_id == ""
        assert r.base_intensity == 0.0
        assert r.seed == 0


class TestDeterminism:

    def test_same_seed_reproduces_z_and_seeds(self):
        a = generate_event_set(count=50, catchment_id="thames", seed=123)
        b = generate_event_set(count=50, catchment_id="thames", seed=123)
        assert [s.base_intensity for s in a] == [s.base_intensity for s in b]
        assert [s.seed for s in a] == [s.seed for s in b]
        assert [s.event_id for s in a] == [s.event_id for s in b]


class TestFloodDrawsUnchanged:
    """The per-event seed must NOT perturb the storm draws.

    The coupling seeds are spawned from a separate SeedSequence stream, so the
    category assignments and base_intensity draws produced by the storm `rng`
    must remain bit-identical to the pre-coupling implementation. This is the
    guard that flood pricing is unaffected by Stage 2.
    """

    def test_base_intensity_matches_legacy_rng_path(self):
        count, seed = 100, 42
        seqs = generate_event_set(count=count, catchment_id="thames", seed=seed)

        # Reproduce the exact pre-coupling draw sequence.
        cats = list(DEFAULT_INTENSITY_WEIGHTS.keys())
        w = np.array([DEFAULT_INTENSITY_WEIGHTS[c] for c in cats], dtype=float)
        probs = w / w.sum()
        rng = np.random.RandomState(seed)
        draws = rng.choice(len(cats), size=count, p=probs)
        legacy_z = []
        for ci in draws:
            mean, std = BASE_INTENSITY_PARAMS.get(cats[ci], (1.0, 0.20))
            legacy_z.append(max(0.1, rng.normal(mean, std)))

        assert [s.base_intensity for s in seqs] == legacy_z
        assert [s.intensity_category for s in seqs] == [cats[c] for c in draws]
