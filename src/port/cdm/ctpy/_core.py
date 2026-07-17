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
