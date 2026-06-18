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
