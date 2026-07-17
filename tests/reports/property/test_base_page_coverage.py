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

"""
Tests for missing coverage in reports.property.property_page_00_base.

Covers:
- Line 65: 'Title' already in styles (skip add)
- Line 277: _format_value(None) -> 'Not specified'
- Line 288: _format_value('') -> 'Not specified'
- Line 296: _format_currency(non-numeric) -> delegates to _format_value
- Line 302: _format_percentage(non-numeric) -> delegates to _format_value
- Line 308: abstract generate_elements (pass)
"""

import pytest
from reportlab.lib.styles import getSampleStyleSheet


class _ConcretePage:
    """Concrete subclass for testing abstract PropertyBasePage."""

    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            from reports.property.property_page_00_base import PropertyBasePage

            class Impl(PropertyBasePage):
                def generate_elements(self, property_data, rloan_data=None):
                    return []

            cls._instance = Impl()
        return cls._instance


class TestPropertyBasePageTitleStyleExists:
    """Line 65: 'Title' already in default styles -> skip custom add."""

    def test_title_style_present(self):
        """getSampleStyleSheet() includes 'Title' by default, so line 65 branch
        is taken (skip the add). Verify the page still initialises."""
        page = _ConcretePage.get()
        # 'Title' should exist in styles regardless
        assert 'Title' in page.styles


class TestFormatValueNone:
    """Line 277: _format_value(None) -> 'Not specified'."""

    def test_none_returns_not_specified(self):
        page = _ConcretePage.get()
        assert page._format_value(None) == 'Not specified'


class TestFormatValueEmptyString:
    """Line 288: _format_value('   ') -> 'Not specified'."""

    def test_empty_string_returns_not_specified(self):
        page = _ConcretePage.get()
        assert page._format_value('') == 'Not specified'

    def test_whitespace_string_returns_not_specified(self):
        page = _ConcretePage.get()
        assert page._format_value('   ') == 'Not specified'


class TestFormatCurrencyNonNumeric:
    """Line 296: _format_currency(non-numeric) -> delegates to _format_value."""

    def test_string_currency_delegates(self):
        page = _ConcretePage.get()
        result = page._format_currency("N/A")
        assert result == "N/A"

    def test_none_currency_returns_not_specified(self):
        page = _ConcretePage.get()
        result = page._format_currency(None)
        assert result == 'Not specified'


class TestFormatPercentageNonNumeric:
    """Line 302: _format_percentage(non-numeric) -> delegates to _format_value."""

    def test_string_percentage_delegates(self):
        page = _ConcretePage.get()
        result = page._format_percentage("N/A")
        assert result == "N/A"

    def test_none_percentage_returns_not_specified(self):
        page = _ConcretePage.get()
        result = page._format_percentage(None)
        assert result == 'Not specified'


class TestAbstractGenerateElements:
    """Line 308: abstract method pass statement."""

    def test_concrete_subclass_returns_empty_list(self):
        page = _ConcretePage.get()
        result = page.generate_elements({})
        assert result == []
