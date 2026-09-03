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

"""Tests for the dataset-mode flag that gates full-dataset-only checks."""

import importlib

import pytest

from tests import _dataset


class TestEphemeralDataset:
    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "Yes"])
    def test_recognised_truthy_values(self, monkeypatch, value):
        monkeypatch.setenv(_dataset.ENV_FLAG, value)
        assert _dataset.ephemeral_dataset() is True

    @pytest.mark.parametrize("value", ["0", "", "no", "false", "maybe"])
    def test_everything_else_is_full_dataset(self, monkeypatch, value):
        monkeypatch.setenv(_dataset.ENV_FLAG, value)
        assert _dataset.ephemeral_dataset() is False

    def test_absent_flag_means_full_dataset(self, monkeypatch):
        """Default must be to RUN the checks. A helper that skipped unless told
        otherwise would silently hollow out the lineage suite — the failure
        mode this exists to prevent."""
        monkeypatch.delenv(_dataset.ENV_FLAG, raising=False)
        assert _dataset.ephemeral_dataset() is False

    def test_whitespace_is_tolerated(self, monkeypatch):
        monkeypatch.setenv(_dataset.ENV_FLAG, "  1  ")
        assert _dataset.ephemeral_dataset() is True


class TestFullDatasetOnlyMark:
    def test_mark_does_not_skip_by_default(self, monkeypatch):
        monkeypatch.delenv(_dataset.ENV_FLAG, raising=False)
        mod = importlib.reload(_dataset)
        assert mod.full_dataset_only.args[0] is False, (
            "the mark would skip on an ordinary full-dataset run"
        )

    def test_mark_skips_when_declared_ephemeral(self, monkeypatch):
        monkeypatch.setenv(_dataset.ENV_FLAG, "1")
        mod = importlib.reload(_dataset)
        assert mod.full_dataset_only.args[0] is True

    def test_reason_names_the_flag_and_says_why(self, monkeypatch):
        """A reader hitting the skip must be able to tell whether it is
        expected without reading the source."""
        monkeypatch.setenv(_dataset.ENV_FLAG, "1")
        mod = importlib.reload(_dataset)
        reason = mod.full_dataset_only.kwargs["reason"]
        assert mod.ENV_FLAG in reason
        assert "tautological" in reason

    @pytest.fixture(autouse=True)
    def _restore(self, monkeypatch):
        yield
        monkeypatch.delenv(_dataset.ENV_FLAG, raising=False)
        importlib.reload(_dataset)
