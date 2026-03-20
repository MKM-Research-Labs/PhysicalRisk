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

"""Tests for sequence record structure and intensity_category round-trip."""

import pytest

from port.src.stressm import GAUGE_SUMMARY_FILENAME
from port.src.storm_multi.core.data_structures import StormSequence
from port.src.storm_multi.generators.batch_generator import generate_event_set
from port.src.storm_multi.utils.serialization import SEQUENCES_FILENAME, load_sequences

import json


# ---------------------------------------------------------------------------
# generate_stressm — sequence record structure
# ---------------------------------------------------------------------------

class TestSequenceRecordStructure:

    @pytest.fixture(scope="class")
    def records(self, gauge_dir, full_run):  # full_run ensures gauge_dir is populated
        with open(gauge_dir / GAUGE_SUMMARY_FILENAME) as f:
            d = json.load(f)
        return d["sequences"]

    def test_all_have_sequence_id(self, records):
        assert all("sequence_id" in r for r in records)

    def test_all_have_sequence_type(self, records):
        valid = {"isolated", "doublet", "cluster", "persistent"}
        assert all(r["sequence_type"] in valid for r in records)

    def test_all_have_intensity_category(self, records):
        valid = {"moderate", "severe", "extreme", "catastrophic"}
        assert all(r["intensity_category"] in valid for r in records)

    def test_all_have_total_precip(self, records):
        assert all("total_precip_mm" in r for r in records)
        assert all(r["total_precip_mm"] > 0 for r in records)

    def test_peaks_length_matches_num_gauges(self, records):
        assert all(len(r["peaks_m"]) == 3 for r in records)

    def test_peak_hours_length_matches_num_gauges(self, records):
        assert all(len(r["peak_hours"]) == 3 for r in records)

    def test_alert_flags_length_matches_num_gauges(self, records):
        assert all(len(r["alert"]) == 3 for r in records)

    def test_warning_flags_length_matches_num_gauges(self, records):
        assert all(len(r["warning"]) == 3 for r in records)

    def test_severe_flags_length_matches_num_gauges(self, records):
        assert all(len(r["severe"]) == 3 for r in records)

    def test_peak_hours_in_valid_range(self, records):
        for r in records:
            assert all(0 <= h <= 167 for h in r["peak_hours"])

    def test_peaks_positive(self, records):
        for r in records:
            assert all(p > 0 for p in r["peaks_m"])

    def test_warning_implies_alert(self, records):
        """Every sequence that breached warning must also have breached alert."""
        for r in records:
            for i in range(3):
                if r["warning"][i]:
                    assert r["alert"][i]

    def test_severe_implies_warning(self, records):
        for r in records:
            for i in range(3):
                if r["severe"][i]:
                    assert r["warning"][i]


# ---------------------------------------------------------------------------
# intensity_category on StormSequence (data structure round-trip)
# ---------------------------------------------------------------------------

class TestIntensityCategoryRoundTrip:

    def test_batch_generator_populates_category(self):
        seqs = generate_event_set(count=20, seed=0)
        valid = {"moderate", "severe", "extreme", "catastrophic"}
        assert all(s.intensity_category in valid for s in seqs)

    def test_to_dict_includes_intensity_category(self):
        seqs = generate_event_set(count=5, seed=1)
        for s in seqs:
            d = s.to_dict()
            assert "intensity_category" in d
            assert d["intensity_category"] == s.intensity_category

    def test_from_dict_round_trip(self):
        seqs = generate_event_set(count=5, seed=2)
        for s in seqs:
            reconstructed = StormSequence.from_dict(s.to_dict())
            assert reconstructed.intensity_category == s.intensity_category

    def test_from_dict_missing_category_defaults_empty(self):
        seqs = generate_event_set(count=1, seed=3)
        d = seqs[0].to_dict()
        del d["intensity_category"]
        reconstructed = StormSequence.from_dict(d)
        assert reconstructed.intensity_category == ""

    def test_serialized_sequences_have_category(self, gauge_dir, full_run):
        seqs = load_sequences(gauge_dir / SEQUENCES_FILENAME)
        valid = {"moderate", "severe", "extreme", "catastrophic"}
        assert all(s.intensity_category in valid for s in seqs)
