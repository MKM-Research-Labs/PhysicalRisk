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

"""Cross-reference lookup builders and ID utilities."""

from .builders import (
    _classify_property_risk,
    build_all_lookups,
    build_gauge_flood_info,
    build_mortgage_lookup,
    build_property_flood_info,
)
from .id_utils import (
    analyze_id_relationships,
    extract_gauge_ids,
    extract_mortgage_ids,
    extract_mortgage_property_ids,
    extract_property_ids,
)

__all__ = [
    'build_mortgage_lookup',
    'build_gauge_flood_info',
    'build_property_flood_info',
    'build_all_lookups',
    'extract_property_ids',
    'extract_mortgage_ids',
    'extract_mortgage_property_ids',
    'extract_gauge_ids',
    'analyze_id_relationships',
]
