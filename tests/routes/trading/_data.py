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
Backward-compatible re-export shim.

After splitting _data.py into _data_part1.py and _data_part2.py, this file
re-exports all public names so existing ``from ._data import ...`` statements
continue to work without changes.
"""

from ._data_part1 import (  # noqa: F401
    GAUGE_WESTMINSTER, GAUGE_CHELSEA, GAUGE_LAMBETH,
    GAUGE_VAUXHALL, GAUGE_WATERLOO, GAUGE_BLACKFRIARS, GAUGE_LONDON,
    ALL_TEST_GAUGE_IDS,
    make_trade, make_gauge_entry,
    SAMPLE_GAUGEHC, SAMPLE_GAUGE_JSON,
)

from ._data_part2 import (  # noqa: F401
    CORE_TRADES, EXTENDED_TRADES, ALL_TRADES, TOTAL_TRADES,
    STORM_PORT_SEVERE, STORM_PORT_ALERT, SAMPLE_PORT_STRESS_STORMS,
    STORM_SEVERE, STORM_WARNING, SAMPLE_STRESS_STORMS,
)
