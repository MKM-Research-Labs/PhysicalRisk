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

"""Circular-arithmetic helpers for compass-bearing angles.

Heading convention used throughout the typhoon model: compass degrees,
0 = North, increasing clockwise. These helpers operate in that space
without ever crossing the 0/360 seam.
"""

__all__ = [
    "wrap_compass_degrees",
    "signed_compass_delta",
]


def wrap_compass_degrees(deg: float) -> float:
    """Wrap an angle to the compass range [0, 360)."""
    return deg % 360.0


def signed_compass_delta(target_deg: float, current_deg: float) -> float:
    """Smallest signed angular delta from current to target, in (-180, 180].

    Positive results indicate a clockwise rotation; negative results are
    counter-clockwise. Useful for circular averaging without 0/360
    wrap-around: for example, the delta from 350 to 10 is +20, not -340.
    """
    raw = (target_deg - current_deg) % 360.0
    return raw if raw <= 180.0 else raw - 360.0
