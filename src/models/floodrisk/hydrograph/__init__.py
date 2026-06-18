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
Per-pulse hydrograph superposition model (v2.2).

Builds compound property hydrographs from individual storm pulses using
gamma-shaped templates, antecedent saturation scaling, linear superposition,
and flow-path infiltration.  Replaces the single-peak / single-shape approach
in velocity.build_property_hydrograph() for multi-storm sequences.
"""

from .gamma import gamma_shape, gamma_shape_array
from .pulse import build_pulse_gauge_hydrograph
from .saturation import compute_saturation_factor, superimpose_pulses
from .infiltration import apply_infiltration
from .compound import build_compound_property_hydrograph
