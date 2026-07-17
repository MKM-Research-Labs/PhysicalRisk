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

"""Coverage expansion tests for ctpy.py — Block B6.

Targets missing lines:
  - 251-252: Exception handler in validate() returns {"validation_error": [str(e)]}
"""

import pytest

from port.cdm.ctpy import CounterpartyCDM


class TestValidateExceptionHandler:

    def test_validate_with_non_dict_returns_validation_error(self):
        """Lines 251-252: passing data that causes an exception in the try
        block returns a validation_error dict instead of raising."""
        cdm = CounterpartyCDM()
        # Passing a list instead of dict — .get() on list raises AttributeError
        result = cdm.validate([1, 2, 3])
        assert "validation_error" in result
        assert isinstance(result["validation_error"], list)
        assert len(result["validation_error"]) > 0

    def test_validate_with_integer_returns_validation_error(self):
        """Another path to trigger the except branch."""
        cdm = CounterpartyCDM()
        result = cdm.validate(42)
        assert "validation_error" in result

    def test_validate_exception_message_is_string(self):
        """The error message should be a string representation of the exception."""
        cdm = CounterpartyCDM()
        result = cdm.validate(None)
        assert "validation_error" in result
        assert isinstance(result["validation_error"][0], str)
