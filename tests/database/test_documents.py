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

"""Tests for the low-level document I/O helpers (legacy loader layer)."""

import json

import pytest

from database.documents import read_json_document, iter_document_names


def test_read_present(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps({"x": 1}))
    assert read_json_document(tmp_path, "a.json") == {"x": 1}


def test_read_missing_returns_none(tmp_path):
    assert read_json_document(tmp_path, "nope.json") is None


def test_read_corrupt_raises(tmp_path):
    (tmp_path / "bad.json").write_text("{not json")
    with pytest.raises(json.JSONDecodeError):
        read_json_document(tmp_path, "bad.json")


def test_iter_names_sorted_skips_index_and_other_ext(tmp_path):
    (tmp_path / "b.json").write_text("{}")
    (tmp_path / "a.json").write_text("{}")
    (tmp_path / "_index.json").write_text("{}")
    (tmp_path / "c.txt").write_text("x")
    assert list(iter_document_names(tmp_path)) == ["a.json", "b.json"]


def test_iter_missing_dir_is_empty(tmp_path):
    assert list(iter_document_names(tmp_path / "nope")) == []
