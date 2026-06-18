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

"""Enumerations for the seismic model configuration."""

from enum import Enum


class DamageState(Enum):
    """The four HAZUS/GEM-style damage states of the fragility chain.

    The integer value is the threshold index: DS0 is the no-collapse floor,
    DS3 (complete / collapse) is the point-of-no-return analogue whose
    frequency the PRS pricer charges as the seismic spread.
    """
    DS0 = 0  # None / Slight
    DS1 = 1  # Moderate
    DS2 = 2  # Extensive
    DS3 = 3  # Complete / collapse


class SoilClass(Enum):
    """Eurocode 8 site classes derived from V_S30 (Appendix C2)."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
