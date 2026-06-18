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

"""Property pricing and basis calculation mixin for PropertyHazardCurveGenerator.

v3.0: Replaced GEV/CDS pricing with simple severe event count.
Spread (bp) = N(severe floods) / N(total scenarios) × 10,000.
Term structure is flat (storms are independent).

Stage 6 (peril outcomes): the pricer emits a ``prs_perils`` block with all
four peril outcomes at the property/BRI node (coupling_spec.md §11.6):

* ``flood_only``    — severe flood triggers (the flood spine, unchanged)
* ``wind_only``     — binary ``is_prs_wind`` damage-onset triggers
* ``flood_or_wind`` — union over the 1:1-paired event set (one denominator)
* ``flood_and_wind``— intersection (inclusion-exclusion: F + W − union)

The wind leg is the binary ``is_prs_wind`` damage-onset trigger — NOT the
continuous wind damage amount. The flood-only ``prs_spread_bps`` /
``term_structure.severe`` (flood spine) is kept unchanged: it still drives the
gauge basis and the flood-vs-gauge spread decomposition. Wind has no gauge
intermediary — it is a pure intersect/union at the property node. Catchments
without a typhoon stage emit no ``prs_perils`` block and are byte-identical to
before (flood-only fallback).
"""

from ._pricing import PricingMixin

__all__ = ["PricingMixin"]
