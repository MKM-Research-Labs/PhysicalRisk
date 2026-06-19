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

"""Public API — portfolio entities (gauges, properties, loans, commercial, counterparties)."""

from __future__ import annotations

from .backend import active_backend
from ._helpers import find_record, list_records


def list_gauges(catchment): return list_records("gauge", catchment)
def get_gauge(catchment, gauge_id): return find_record("gauge", catchment, gauge_id)
def save_gauges(catchment, gauges): active_backend().save("gauge", catchment, gauges)

def list_properties(catchment): return list_records("property", catchment)
def get_property(catchment, property_id): return find_record("property", catchment, property_id)
def save_properties(catchment, properties): active_backend().save("property", catchment, properties)

def list_loans(catchment): return list_records("loan", catchment)
def get_loan(catchment, loan_id): return find_record("loan", catchment, loan_id)
def save_loans(catchment, loans): active_backend().save("loan", catchment, loans)

def list_commercial(catchment): return list_records("commercial", catchment)
def get_commercial(catchment, asset_id): return find_record("commercial", catchment, asset_id)
def save_commercial(catchment, assets): active_backend().save("commercial", catchment, assets)

def list_commercial_loans(catchment): return list_records("commercial_loan", catchment)
def get_commercial_loan(catchment, loan_id): return find_record("commercial_loan", catchment, loan_id)
def save_commercial_loans(catchment, loans): active_backend().save("commercial_loan", catchment, loans)

def list_counterparties(catchment): return list_records("counterparty", catchment)
def get_counterparty(catchment, counterparty_id): return find_record("counterparty", catchment, counterparty_id)
def save_counterparties(catchment, cps): active_backend().save("counterparty", catchment, cps)
