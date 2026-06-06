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
Counterparty portfolio generator.

Generates synthetic counterparty data following the CounterpartyCDM schema.
Counterparties represent trading partners for PRS instruments.

Trading rules
-------------
* **Gauge PRS** trades are between the trader (MKM Research Labs) and an
  *external* counterparty drawn from ``_ALL_COUNTERPARTIES`` (banks,
  insurers, reinsurers, etc.) with random ``CTPY-{8hex}`` IDs.
* **Property PRS** trades are between the trader and the **REIT client
  exclusively** — a fixed counterparty ``CTPY-REIT-001`` ("Thames
  Property REIT") that is *always* emitted by the generator regardless
  of the random external set.

This module therefore prepends a deterministic REIT entry before
generating the random external pool, so ``counterparty.json`` always
contains the counterpart that ``book_property.py`` references.
"""

from port.src.counterparty._data import (
    _ADDRESSES,
    _ALL_COUNTERPARTIES,
    _BANK_NAMES,
    _CONTACTS,
    _INSURER_NAMES,
    _OTHER_NAMES,
    _RATING_AGENCIES,
    _RATINGS,
    _REINSURER_NAMES,
    _SORT_CODES,
)
from port.src.counterparty._generator import (
    CounterpartyPortfolioGenerator,
    generate_counterparties,
)

__all__ = [
    "CounterpartyPortfolioGenerator",
    "generate_counterparties",
]
