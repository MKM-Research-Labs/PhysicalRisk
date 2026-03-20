# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Tests for _generate_elements and generate_report."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from .conftest import _make_generator


class TestGenerateElements:
    """Tests for _generate_elements."""

    def test_returns_list(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        elements = gen._generate_elements(minimal_flood_data, ["title"])
        assert isinstance(elements, list)

    def test_empty_page_list(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        elements = gen._generate_elements(minimal_flood_data, [])
        assert elements == []

    def test_unknown_page_skipped(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        elements = gen._generate_elements(minimal_flood_data, ["nonexistent_page_xyz"])
        assert isinstance(elements, list)
        assert len(elements) == 0

    def test_mixed_valid_and_unknown_pages(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        elements = gen._generate_elements(minimal_flood_data, ["title", "bogus_page_abc"])
        assert len(elements) > 0

    def test_multiple_pages_inserts_page_breaks(self, tmp_path, minimal_flood_data):
        from reportlab.platypus import PageBreak
        gen = _make_generator(tmp_path)
        elements = gen._generate_elements(
            minimal_flood_data, ["title", "executive_summary"]
        )
        has_break = any(isinstance(e, PageBreak) for e in elements)
        assert has_break

    def test_first_page_no_page_break(self, tmp_path, minimal_flood_data):
        from reportlab.platypus import PageBreak
        gen = _make_generator(tmp_path)
        elements = gen._generate_elements(minimal_flood_data, ["title"])
        assert not any(isinstance(e, PageBreak) for e in elements)

    def test_exception_in_page_continues(self, tmp_path, minimal_flood_data):
        """If one page raises, the remainder are still processed."""
        gen = _make_generator(tmp_path)
        bad_page = MagicMock()
        bad_page.generate_elements.side_effect = RuntimeError("boom")
        gen.pages["_bad"] = bad_page
        elements = gen._generate_elements(minimal_flood_data, ["_bad", "title"])
        assert isinstance(elements, list)
        assert len(elements) > 0


class TestGenerateReport:
    """Tests for generate_report — the primary public method."""

    def test_returns_path(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        result = gen.generate_report(minimal_flood_data)
        assert isinstance(result, Path)

    def test_pdf_exists(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(minimal_flood_data)
        assert path.exists()

    def test_pdf_non_empty(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(minimal_flood_data)
        assert path.stat().st_size > 0

    def test_pdf_suffix(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(minimal_flood_data)
        assert path.suffix == ".pdf"

    def test_custom_output_filename(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(minimal_flood_data, output_filename="my_report.pdf")
        assert path.name == "my_report.pdf"
        assert path.exists()

    def test_custom_pages_to_include(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(
            minimal_flood_data, pages_to_include=["title", "appendix"]
        )
        assert path.exists()

    def test_auto_select_pages_when_none(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        with patch.object(gen, "_auto_select_pages", wraps=gen._auto_select_pages) as spy:
            gen.generate_report(minimal_flood_data, pages_to_include=None)
        spy.assert_called_once()

    def test_auto_select_skipped_when_provided(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        with patch.object(gen, "_auto_select_pages", wraps=gen._auto_select_pages) as spy:
            gen.generate_report(minimal_flood_data, pages_to_include=["title"])
        spy.assert_not_called()

    def test_full_data_report(self, tmp_path, full_flood_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(full_flood_data)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_empty_flood_data(self, tmp_path):
        gen = _make_generator(tmp_path)
        path = gen.generate_report({})
        assert path.exists()
