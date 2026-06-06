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
Model parameter registry.

All hard-coded analytical parameters for the MKM model library live here.
Grouped by model subsystem. Model source files import from this module
rather than defining constants inline.

Subsections:
    PRS Basis Waterfall       — prs_analytical.py
    Depth-Damage Curve        — floodrisk/depth_damage.py
    Flood Velocity / Manning  — floodrisk/velocity.py
    Property Valuation        — valuation/property_value.py
    Insurance Premium         — valuation/insurance.py
"""

from config.damage import DAMAGE_POINTS, DEPTH_POINTS  # noqa: F401

from config.models._flood import *  # noqa: F401,F403
from config.models._valuation import *  # noqa: F401,F403
from config.models._misc import *  # noqa: F401,F403
