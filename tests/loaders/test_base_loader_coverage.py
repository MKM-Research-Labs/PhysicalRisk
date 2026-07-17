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

"""Tests for BaseLoader missing coverage lines: 73, 78, 99, 155, 159, 163, 167."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from loaders.base_loader import BaseLoader


# Concrete subclass for testing abstract methods and compatibility aliases
class _StubLoader(BaseLoader[Dict[str, Any]]):
    ENTITY_NAME = 'stub'
    DEFAULT_FILENAME = 'stub.json'
    CONTAINER_KEYS = ['items']

    def get_entity_id(self, entity):
        return entity.get('id')

    def get_entity_summary(self, entity):
        return {'id': entity.get('id'), 'name': entity.get('name')}


def _write(path: Path, data) -> Path:
    path.write_text(json.dumps(data))
    return path


class TestAbstractMethodsCovered:
    """Lines 73, 78: abstract pass stmts are executed via concrete subclass."""

    def test_get_entity_id_called(self, tmp_path):
        _write(tmp_path / 'stub.json', {'items': [{'id': 'A', 'name': 'Alpha'}]})
        loader = _StubLoader(tmp_path)
        assert loader.find_by_id('A') is not None

    def test_get_entity_summary_called(self, tmp_path):
        _write(tmp_path / 'stub.json', {'items': [{'id': 'B', 'name': 'Beta'}]})
        loader = _StubLoader(tmp_path)
        summaries = loader.list_all()
        assert summaries[0]['id'] == 'B'


class TestNormalizeNonListNonDict:
    """Line 99: _normalize_to_list returns [] for non-list, non-dict data (e.g. int, string)."""

    def test_normalize_integer_returns_empty(self, tmp_path):
        _write(tmp_path / 'stub.json', 42)
        loader = _StubLoader(tmp_path)
        result = loader.load_all()
        assert result == []

    def test_normalize_string_returns_empty(self, tmp_path):
        _write(tmp_path / 'stub.json', '"hello"')
        loader = _StubLoader(tmp_path)
        # json.load will give a string — _normalize_to_list should return []
        result = loader._normalize_to_list("hello")
        assert result == []

    def test_normalize_true_returns_empty(self):
        loader = _StubLoader(Path('/nonexistent'))
        assert loader._normalize_to_list(True) == []

    def test_normalize_float_returns_empty(self):
        loader = _StubLoader(Path('/nonexistent'))
        assert loader._normalize_to_list(3.14) == []


class TestCompatibilityAliases:
    """Lines 155, 159, 163, 167: compatibility alias methods."""

    def test_extract_id_delegates_to_get_entity_id(self, tmp_path):
        """Line 155: _extract_id calls get_entity_id."""
        _write(tmp_path / 'stub.json', {'items': [{'id': 'X'}]})
        loader = _StubLoader(tmp_path)
        entity = {'id': 'X'}
        assert loader._extract_id(entity) == 'X'

    def test_create_summary_delegates_to_get_entity_summary(self, tmp_path):
        """Line 159: _create_summary calls get_entity_summary."""
        loader = _StubLoader(tmp_path)
        entity = {'id': 'Y', 'name': 'Ypsilon'}
        summary = loader._create_summary(entity)
        assert summary == {'id': 'Y', 'name': 'Ypsilon'}

    def test_get_container_keys_returns_class_attr(self, tmp_path):
        """Line 163: _get_container_keys returns CONTAINER_KEYS."""
        loader = _StubLoader(tmp_path)
        assert loader._get_container_keys() == ['items']

    def test_get_file_status_delegates_to_get_status(self, tmp_path):
        """Line 167: get_file_status is alias for get_status."""
        _write(tmp_path / 'stub.json', {'items': []})
        loader = _StubLoader(tmp_path)
        status = loader.get_file_status()
        assert status['entity_name'] == 'stub'
        assert status['exists'] is True
        assert 'path' in status
