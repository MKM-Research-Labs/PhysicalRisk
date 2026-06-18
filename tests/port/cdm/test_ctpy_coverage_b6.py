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
