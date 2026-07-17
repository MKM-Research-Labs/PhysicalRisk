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

"""Coverage tests for FloodPredictor model/summary loading error paths."""

import logging

import pytest

from models.stress.flood_classifier._predictor import FloodPredictor


class TestFloodPredictorLoading:
    def test_load_model_raises_on_version_mismatch(self, tmp_path, monkeypatch):
        # The .joblib exists but joblib.load raises a version-mismatch error
        # (ValueError) -> wrapped as a friendly RuntimeError.
        (tmp_path / "G1.joblib").write_bytes(b"\x00")
        from models.stress.flood_classifier import _predictor

        def _boom(_path):
            raise ValueError("incompatible numpy dtype")

        monkeypatch.setattr(_predictor.joblib, "load", _boom)
        pred = FloodPredictor(tmp_path)
        with pytest.raises(RuntimeError, match="Cannot load classifier"):
            pred._load_model("G1")  # lines 63-68

    def test_load_summary_missing_falls_back_with_warning(self, tmp_path, caplog):
        pred = FloodPredictor(tmp_path)  # no training_summary.json
        with caplog.at_level(logging.WARNING):
            summary = pred._load_summary()
        assert summary == {"gauges": []}            # line 84
        assert "training_summary.json not found" in caplog.text  # line 78
