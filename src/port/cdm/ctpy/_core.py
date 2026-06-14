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
Counterparty / Party Common Data Model (CDM) implementation.

Based on FINOS Common Domain Model Party / Counterparty concepts. Provides a
standardized data model for legal entities and their roles as counterparties
on trades, aligned with CDM usage of Party, Counterparty and
CounterpartyRoleEnum (Party1 / Party2).
"""

from typing import Dict

from ..base import BaseCDM
from ._mapping import _CounterpartyMappingMixin
from ._schema import COUNTERPARTY_SCHEMA


class CounterpartyCDM(_CounterpartyMappingMixin, BaseCDM):
    """
    Counterparty / Party Common Data Model (CDM) implementation.

    Provides a standardized schema and data transformation methods
    for counterparties on trades, following FINOS CDM patterns for
    Party and Counterparty.
    """

    def __init__(self):
        """Initialize the Counterparty CDM with schema definition."""
        self._schema = COUNTERPARTY_SCHEMA

    @property
    def schema(self) -> Dict:
        """Return the CDM schema."""
        return self._schema
