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

"""Book-generator shared constants (re-exported from config.port)."""

from config.port import (  # noqa: F401
    DEFAULT_YIELD_CURVE,
    NOTIONALS,
    RECOVERY,
    SPREAD_OFFSET_MAX,
    SPREAD_OFFSET_MIN,
    TENORS,
    TRIGGER_RATE_KEY,
    TRIGGERS,
)

# The REIT is the fixed counterparty for ALL property PRS trades — it must
# never appear in the gauge-PRS counterparty pool. _load_counterparties is
# only called by gauge-PRS books (book.py / book_thames.py); the property
# book hardcodes the REIT entry itself.
_REIT_PARTY_ID = "CTPY-REIT-001"
