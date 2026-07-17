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

"""Cross-reference lookup builders and ID utilities."""

from .builders import (
    _classify_property_risk,
    build_all_lookups,
    build_gauge_flood_info,
    build_rloan_lookup,
    build_property_flood_info,
)
from .id_utils import (
    analyze_id_relationships,
    extract_gauge_ids,
    extract_rloan_ids,
    extract_rloan_property_ids,
    extract_property_ids,
)

__all__ = [
    'build_rloan_lookup',
    'build_gauge_flood_info',
    'build_property_flood_info',
    'build_all_lookups',
    'extract_property_ids',
    'extract_rloan_ids',
    'extract_rloan_property_ids',
    'extract_gauge_ids',
    'analyze_id_relationships',
]
