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

"""``database`` — the single data-access utility.

The whole codebase calls the intent-named functions re-exported here; this package is
the only place that knows whether data lives in JSON files or PostgreSQL. Swapping
backends is one call to ``configure_backend`` and changes no caller.

Per project rule 4 this module contains NO function definitions — only re-exports.
Implementations live in the domain submodules; see ``src/database/README.md``.
"""

from __future__ import annotations

from .base import Repository
from .backend import configure_backend
from .file_repo import FileRepository
from .memory_repo import InMemoryRepository

from .meta import catchments, ping
from .portfolio import (
    list_gauges, get_gauge, save_gauges, get_gauge_portfolio,
    list_properties, get_property, save_properties, get_property_portfolio,
    list_loans, get_loan, save_loans, get_loan_portfolio,
    list_commercial, get_commercial, save_commercial, get_commercial_portfolio,
    list_commercial_loans, get_commercial_loan, save_commercial_loans,
    list_counterparties, get_counterparty, save_counterparties,
)
from .hazard import (
    get_gauge_hazard_curves, save_gauge_hazard_curves,
    get_property_hazard_curves, save_property_hazard_curves,
    get_commercial_hazard_curves, save_commercial_hazard_curves,
)
from .timeseries import (
    get_property_timeseries, iter_property_timeseries_ids, save_property_timeseries,
    property_timeseries_exists, get_portfolio_flood_summary,
    get_commercial_timeseries, iter_commercial_timeseries_ids, save_commercial_timeseries,
    commercial_timeseries_exists,
    get_gauge_timeseries, gauge_timeseries_exists, iter_gauge_timeseries_ids,
    save_gauge_timeseries,
    get_gauge_history, iter_gauge_history_ids, save_gauge_history,
)
from .storms import (
    get_storm_sequences, save_storm_sequences, get_legacy_storm_sequences,
    list_stress_storms, get_stress_storm, save_stress_storm,
    get_stress_storm_index, get_legacy_stress_storms,
    list_sequence_gauges, get_sequence_gauge, save_sequence_gauge,
    typhoon_events_exist, get_typhoon_event, iter_typhoon_event_ids, save_typhoon_event,
    get_fire_results, save_fire_results, get_seismic_results, save_seismic_results,
)
from .trading import (
    list_prs_trades, iter_prs_trade_ids, get_prs_trade, commit_prs_trade,
    get_trade_marks, save_trade_marks, set_trade_status,
    get_market_state, save_market_state,
    list_eod_snapshots, get_eod_snapshot, save_eod_snapshot,
)
from .classifiers import (
    list_classifier_ids, get_classifier, save_classifier, delete_classifier,
)
from .documents import read_json_document, iter_document_names

__all__ = [
    # backends & lifecycle
    "Repository", "FileRepository", "InMemoryRepository", "configure_backend",
    "catchments", "ping",
    # portfolio
    "list_gauges", "get_gauge", "save_gauges", "get_gauge_portfolio",
    "list_properties", "get_property", "save_properties", "get_property_portfolio",
    "list_loans", "get_loan", "save_loans", "get_loan_portfolio",
    "list_commercial", "get_commercial", "save_commercial", "get_commercial_portfolio",
    "list_commercial_loans", "get_commercial_loan", "save_commercial_loans",
    "list_counterparties", "get_counterparty", "save_counterparties",
    # hazard
    "get_gauge_hazard_curves", "save_gauge_hazard_curves",
    "get_property_hazard_curves", "save_property_hazard_curves",
    "get_commercial_hazard_curves", "save_commercial_hazard_curves",
    # timeseries
    "get_property_timeseries", "iter_property_timeseries_ids", "save_property_timeseries",
    "property_timeseries_exists", "get_portfolio_flood_summary",
    "get_commercial_timeseries", "iter_commercial_timeseries_ids", "save_commercial_timeseries",
    "commercial_timeseries_exists",
    "get_gauge_timeseries", "gauge_timeseries_exists", "iter_gauge_timeseries_ids",
    "save_gauge_timeseries",
    "get_gauge_history", "iter_gauge_history_ids", "save_gauge_history",
    # storms / perils
    "get_storm_sequences", "save_storm_sequences", "get_legacy_storm_sequences",
    "list_stress_storms", "get_stress_storm", "save_stress_storm",
    "get_stress_storm_index", "get_legacy_stress_storms",
    "list_sequence_gauges", "get_sequence_gauge", "save_sequence_gauge",
    "typhoon_events_exist", "get_typhoon_event", "iter_typhoon_event_ids",
    "save_typhoon_event",
    "get_fire_results", "save_fire_results", "get_seismic_results", "save_seismic_results",
    # trading
    "list_prs_trades", "iter_prs_trade_ids", "get_prs_trade", "commit_prs_trade",
    "get_trade_marks", "save_trade_marks", "set_trade_status",
    "get_market_state", "save_market_state",
    "list_eod_snapshots", "get_eod_snapshot", "save_eod_snapshot",
    # classifiers
    "list_classifier_ids", "get_classifier", "save_classifier", "delete_classifier",
    # low-level document I/O (legacy loader layer)
    "read_json_document", "iter_document_names",
]
