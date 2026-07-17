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
Data formatting utilities for the visualization system.

``DataFormatter`` composes the value and physical-quantity formatter mixins.
"""

from ._value import _ValueFormattersMixin
from ._physical import _PhysicalFormattersMixin


class DataFormatter(_ValueFormattersMixin, _PhysicalFormattersMixin):
    """Utility class for consistent data formatting across the visualization system."""


# Convenience functions for backward compatibility
safe_format_float = DataFormatter.safe_format_float
format_currency = DataFormatter.format_currency
format_percentage = DataFormatter.format_percentage
format_coordinates = DataFormatter.format_coordinates
format_date = DataFormatter.format_date
format_address = DataFormatter.format_address
