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

from port.src.stressm import GAUGE_SUMMARY_DIR
from pathlib import Path
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
        with open(gauge_dir / GAUGE_SUMMARY_DIR / "_index.json") as f:
            d = json.load(f)
        return d["sequences"]

    @pytest.fixture(scope="class")
    def gauge_records(self, gauge_dir, full_run):
        """Load per-gauge sequence files from the split directory."""
        sg_dir = gauge_dir / GAUGE_SUMMARY_DIR
        gauges = {}
        for p in sg_dir.iterdir():
            if p.name == "_index.json":
                continue
            with open(p) as f:
                gd = json.load(f)
            gauges[gd["gauge_id"]] = gd["sequences"]
        return gauges

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

    def test_gauge_file_count_matches_num_gauges(self, gauge_records):
        assert len(gauge_records) == 3

    def test_per_gauge_sequence_count(self, records, gauge_records):
        for gid, seqs in gauge_records.items():
            assert len(seqs) == len(records), f"{gid} has {len(seqs)} seqs, expected {len(records)}"

    def test_per_gauge_records_have_peak(self, gauge_records):
        for gid, seqs in gauge_records.items():
            assert all("peak_m" in s for s in seqs), f"{gid} missing peak_m"

    def test_per_gauge_records_have_peak_hour(self, gauge_records):
        for gid, seqs in gauge_records.items():
            assert all("peak_hour" in s for s in seqs), f"{gid} missing peak_hour"

    def test_per_gauge_records_have_alert_flags(self, gauge_records):
        for gid, seqs in gauge_records.items():
            assert all("alert" in s for s in seqs), f"{gid} missing alert"

    def test_peak_hours_in_valid_range(self, gauge_records):
        for gid, seqs in gauge_records.items():
            for s in seqs:
                assert 0 <= s["peak_hour"] <= 167, f"{gid} peak_hour {s['peak_hour']} out of range"

    def test_peaks_positive(self, gauge_records):
        for gid, seqs in gauge_records.items():
            assert all(s["peak_m"] > 0 for s in seqs), f"{gid} has non-positive peak"

    def test_warning_implies_alert(self, gauge_records):
        """Every sequence that breached warning must also have breached alert."""
        for gid, seqs in gauge_records.items():
            for s in seqs:
                if s["warning"]:
                    assert s["alert"], f"{gid} {s['sequence_id']} warning without alert"

    def test_severe_implies_warning(self, gauge_records):
        for gid, seqs in gauge_records.items():
            for s in seqs:
                if s["severe"]:
                    assert s["warning"], f"{gid} {s['sequence_id']} severe without warning"


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
