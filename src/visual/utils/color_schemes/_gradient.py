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

"""Gradient interpolation and hex/RGB conversion mixin for ColorSchemes."""

import colorsys
from typing import List, Tuple


class _GradientMixin:
    """Gradient-colour generation and hex/RGB conversion helpers."""

    @classmethod
    def create_gradient_color(cls, value: float, min_value: float, max_value: float,
                            start_color: str = '#4CAF50', end_color: str = '#F44336') -> str:
        """
        Create a gradient color based on a value within a range.

        Args:
            value: Current value
            min_value: Minimum value in range
            max_value: Maximum value in range
            start_color: Color for minimum value (hex)
            end_color: Color for maximum value (hex)

        Returns:
            Interpolated hex color code
        """
        if max_value <= min_value:
            return start_color

        # Normalize value to 0-1 range
        normalized = max(0, min(1, (value - min_value) / (max_value - min_value)))

        # Convert hex to RGB
        start_rgb = cls._hex_to_rgb(start_color)
        end_rgb = cls._hex_to_rgb(end_color)

        # Interpolate RGB values
        interpolated_rgb = [
            int(start_rgb[i] + (end_rgb[i] - start_rgb[i]) * normalized)
            for i in range(3)
        ]

        # Convert back to hex
        return cls._rgb_to_hex(interpolated_rgb)

    @classmethod
    def create_hsv_gradient(cls, value: float, min_value: float, max_value: float,
                          start_hue: float = 0.3, end_hue: float = 0.0) -> str:
        """
        Create a gradient color using HSV color space.

        Args:
            value: Current value
            min_value: Minimum value in range
            max_value: Maximum value in range
            start_hue: Starting hue (0-1, where 0.3 is green, 0 is red)
            end_hue: Ending hue

        Returns:
            Hex color code
        """
        if max_value <= min_value:
            rgb = colorsys.hsv_to_rgb(start_hue, 0.8, 0.9)
        else:
            # Normalize value to 0-1 range
            normalized = max(0, min(1, (value - min_value) / (max_value - min_value)))

            # Interpolate hue
            hue = start_hue + (end_hue - start_hue) * normalized

            # Convert HSV to RGB
            rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)

        # Convert to hex
        return f'#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}'

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    @staticmethod
    def _rgb_to_hex(rgb: List[int]) -> str:
        """Convert RGB list to hex color."""
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
