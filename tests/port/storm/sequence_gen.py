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

"""Tests for SequenceGenerator (sequence_generator.py)."""

import pytest
import numpy as np

from port.src.storm_multi.generators.sequence_generator import SequenceGenerator
from port.src.storm_multi.core.data_structures import SequenceType, StormSequence
from catch.thames.storm import BASE_PRECIPITATION_MM as THAMES_BASE_PRECIP
from catch.halong.storm import BASE_PRECIPITATION_MM as HALONG_BASE_PRECIP


class TestSequenceGeneratorInit:

    def test_default_catchment(self):
        gen = SequenceGenerator()
        assert gen.catchment_id == "thames"
        assert gen.base_precipitation == THAMES_BASE_PRECIP

    def test_custom_catchment(self):
        """Halong has its own storm.py with a different BASE_PRECIPITATION_MM."""
        gen = SequenceGenerator(catchment_id="halong")
        assert gen.catchment_id == "halong"
        assert gen.base_precipitation == HALONG_BASE_PRECIP

    def test_unknown_catchment_defaults_to_35(self):
        """No storm.py for the catchment → 35.0 mm fallback."""
        gen = SequenceGenerator(catchment_id="unknown_river")
        assert gen.base_precipitation == 35.0

    def test_seeded_reproducibility(self):
        """Same seed → same sequence."""
        gen1 = SequenceGenerator(seed=42)
        gen2 = SequenceGenerator(seed=42)
        seq1 = gen1.generate("moderate", 1.0)
        seq2 = gen2.generate("moderate", 1.0)
        assert seq1.num_storms == seq2.num_storms
        assert seq1.sequence_type == seq2.sequence_type


class TestSequenceGeneratorGenerate:

    def test_returns_storm_sequence(self):
        gen = SequenceGenerator(seed=1)
        result = gen.generate("moderate", 1.0)
        assert isinstance(result, StormSequence)

    def test_isolated_force(self):
        """force_sequence_type='isolated' → always isolated."""
        gen = SequenceGenerator(seed=5)
        result = gen.generate("severe", 1.5, force_sequence_type="isolated")
        assert result.sequence_type == SequenceType.ISOLATED.value
        assert result.num_storms == 1

    def test_doublet_force(self):
        """force_sequence_type='doublet' → always doublet."""
        gen = SequenceGenerator(seed=5)
        result = gen.generate("severe", 1.5, force_sequence_type="doublet")
        assert result.sequence_type == SequenceType.DOUBLET.value
        assert result.num_storms == 2

    def test_sequence_fits_in_window(self):
        """All sequences must have total_duration <= 168h."""
        gen = SequenceGenerator(seed=99)
        for cat in ["moderate", "severe", "extreme"]:
            result = gen.generate(cat, 1.0)
            assert result.total_duration_hours <= 168.0

    def test_minimal_category_often_isolated(self):
        """Minimal intensity (5% sequence probability) mostly produces isolated."""
        gen = SequenceGenerator(seed=42)
        results = [gen.generate("minimal", 0.3) for _ in range(20)]
        isolated = sum(1 for r in results if r.num_storms == 1)
        assert isolated >= 10  # should be mostly isolated

    def test_storms_have_correct_fields(self):
        gen = SequenceGenerator(seed=7)
        result = gen.generate("severe", 1.5, force_sequence_type="doublet")
        for storm in result.storms:
            assert storm.duration_hours > 0
            assert storm.intensity_factor > 0
            assert storm.precipitation_mm > 0
            assert 0 <= storm.peak_position <= 1

    def test_catchment_id_in_storms(self):
        gen = SequenceGenerator(catchment_id="rhine", seed=3)
        result = gen.generate("moderate", 1.0, force_sequence_type="isolated")
        assert result.storms[0].catchment_id == "rhine"

    def test_multiple_calls(self):
        """Generate multiple sequences without error."""
        gen = SequenceGenerator(seed=0)
        for i in range(10):
            result = gen.generate("moderate", 1.0 + i * 0.1)
            assert isinstance(result, StormSequence)
            assert result.num_storms >= 1

    def test_cluster_sequence(self):
        gen = SequenceGenerator(seed=42)
        result = gen.generate("moderate", 1.0, force_sequence_type="cluster")
        # May fall back to isolated if cluster can't fit in window
        assert result.sequence_type in (SequenceType.CLUSTER.value, SequenceType.ISOLATED.value)

    def test_persistent_sequence(self):
        gen = SequenceGenerator(seed=42)
        result = gen.generate("moderate", 1.0, force_sequence_type="persistent")
        # May fall back to isolated if persistent can't fit in window
        assert result.sequence_type in (SequenceType.PERSISTENT.value, SequenceType.ISOLATED.value)

    def test_aggregate_stats(self):
        gen = SequenceGenerator(seed=10)
        result = gen.generate("moderate", 1.0, force_sequence_type="doublet")
        assert result.max_intensity_factor >= result.avg_intensity_factor
        assert result.total_precipitation_mm > 0
        assert result.cumulative_intensity_factor == pytest.approx(
            sum(s.intensity_factor for s in result.storms), rel=1e-5
        )


class TestBuildIsolated:
    """Tests for isolated (single-storm) sequences via _build_sequence."""

    def test_isolated_has_one_storm(self):
        from port.src.storm_multi.core.data_structures import SequenceType
        gen = SequenceGenerator(seed=123)
        seq_id = "STORM-test0001"
        result = gen._build_sequence(
            seq_id, SequenceType.ISOLATED, 1, "moderate", 1.0, "2026-01-01T00:00:00"
        )
        assert isinstance(result, StormSequence)
        assert result.num_storms == 1
        assert len(result.storms) == 1
        assert len(result.inter_storm_gaps_hours) == 0

    def test_isolated_duration_clamped(self):
        """Duration must not exceed MAX_PRECIP_END_HOUR (156)."""
        from port.src.storm_multi.core.data_structures import SequenceType
        from port.src.storm_multi.utils.validation import MAX_PRECIP_END_HOUR
        gen = SequenceGenerator(seed=123)
        result = gen._build_sequence(
            "STORM-clamp001", SequenceType.ISOLATED, 1, "catastrophic", 3.0, "2026-01-01T00:00:00"
        )
        assert result.storms[0].duration_hours <= MAX_PRECIP_END_HOUR
