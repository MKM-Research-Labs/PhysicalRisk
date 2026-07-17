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

from .auth import (
    check_permission,
    create_user,
    get_password_hash,
    get_user,
    get_user_permissions,
    is_admin,
    list_functions,
    list_users,
    seed_function_registry,
    seed_functions,
    set_password_hash,
    set_permission,
    set_user_active,
)
from .backend import backend_configured, configure_backend
from .base import Repository
from .classifiers import (
    delete_classifier,
    delete_classifier_timings,
    delete_classifier_training_summary,
    get_classifier,
    get_classifier_timings,
    get_classifier_training_summary,
    list_classifier_ids,
    save_classifier,
    save_classifier_timings,
    save_classifier_training_summary,
)
from .context import active_catchment, catchment_context
from .documents import iter_document_names, read_json_document
from .file_repo import FileRepository
from .hazard import (
    get_commercial_hazard_curves,
    get_gauge_hazard_curves,
    get_property_hazard_curves,
    save_commercial_hazard_curves,
    save_gauge_hazard_curves,
    save_property_hazard_curves,
)
from .memory_repo import InMemoryRepository
from .meta import catchments, object_store_reachable, ping, postgres_reachable
from .portfolio import (
    get_commercial,
    get_commercial_loan,
    get_commercial_loan_portfolio,
    get_commercial_portfolio,
    get_counterparty,
    get_counterparty_portfolio,
    get_gauge,
    get_gauge_portfolio,
    get_loan,
    get_loan_portfolio,
    get_property,
    get_property_portfolio,
    list_commercial,
    list_commercial_loans,
    list_counterparties,
    list_gauges,
    list_loans,
    list_properties,
    save_commercial,
    save_commercial_loans,
    save_counterparties,
    save_gauges,
    save_loans,
    save_properties,
)
from .storms import (
    clear_sequence_gauges,
    get_fire_results,
    get_legacy_storm_sequences,
    get_legacy_stress_storms,
    get_seismic_results,
    get_sequence_gauge,
    get_sequence_summary,
    get_storm_sequences,
    get_stress_storm,
    get_stress_storm_index,
    get_typhoon_event,
    iter_typhoon_event_ids,
    list_sequence_gauges,
    list_stress_storms,
    save_fire_results,
    save_seismic_results,
    save_sequence_gauge,
    save_sequence_summary,
    save_storm_sequences,
    save_stress_storm,
    save_typhoon_event,
    storm_sequences_exists,
    typhoon_events_exist,
)
from .timeseries import (
    clear_commercial_timeseries,
    clear_property_timeseries,
    commercial_timeseries_exists,
    delete_gauge_history,
    delete_gauge_timeseries,
    gauge_timeseries_exists,
    get_commercial_portfolio_flood_summary,
    get_commercial_timeseries,
    get_gauge_history,
    get_gauge_timeseries,
    get_portfolio_flood_summary,
    get_property_timeseries,
    iter_commercial_timeseries_ids,
    iter_gauge_history_ids,
    iter_gauge_timeseries_ids,
    iter_property_timeseries_ids,
    property_timeseries_exists,
    save_commercial_portfolio_flood_summary,
    save_commercial_timeseries,
    save_gauge_history,
    save_gauge_timeseries,
    save_portfolio_flood_summary,
    save_property_timeseries,
)
from .trading import (
    clear_eod_snapshots,
    commit_prs_trade,
    delete_eod_snapshot,
    get_eod_snapshot,
    get_hazard_curve_history,
    get_market_state,
    get_prs_trade,
    get_trade_marks,
    get_trade_pnl_history,
    iter_eod_snapshots,
    iter_prs_trade_ids,
    list_eod_snapshots,
    list_prs_trades,
    save_eod_snapshot,
    save_hazard_curve_history,
    save_market_state,
    save_prs_trade,
    save_trade_marks,
    save_trade_pnl_history,
    set_trade_status,
)

__all__ = [
    # RBAC (WP5) — application-level permission checks + admin management (pg-only)
    "seed_function_registry", "seed_functions", "list_functions", "is_admin",
    "create_user", "get_user", "set_user_active", "list_users",
    "set_permission", "check_permission", "get_user_permissions",
    "set_password_hash", "get_password_hash",
    # backends & lifecycle
    "Repository", "FileRepository", "InMemoryRepository", "configure_backend",
    "backend_configured",
    "active_catchment", "catchment_context",
    "catchments", "ping", "postgres_reachable", "object_store_reachable",
    # portfolio
    "list_gauges", "get_gauge", "save_gauges", "get_gauge_portfolio",
    "list_properties", "get_property", "save_properties", "get_property_portfolio",
    "list_loans", "get_loan", "save_loans", "get_loan_portfolio",
    "list_commercial", "get_commercial", "save_commercial", "get_commercial_portfolio",
    "list_commercial_loans", "get_commercial_loan", "save_commercial_loans",
    "get_commercial_loan_portfolio",
    "list_counterparties", "get_counterparty", "save_counterparties",
    "get_counterparty_portfolio",
    # hazard
    "get_gauge_hazard_curves", "save_gauge_hazard_curves",
    "get_property_hazard_curves", "save_property_hazard_curves",
    "get_commercial_hazard_curves", "save_commercial_hazard_curves",
    # timeseries
    "get_property_timeseries", "iter_property_timeseries_ids", "save_property_timeseries",
    "property_timeseries_exists", "get_portfolio_flood_summary",
    "save_portfolio_flood_summary",
    "get_commercial_portfolio_flood_summary", "save_commercial_portfolio_flood_summary",
    "get_commercial_timeseries", "iter_commercial_timeseries_ids", "save_commercial_timeseries",
    "commercial_timeseries_exists",
    "get_gauge_timeseries", "gauge_timeseries_exists", "iter_gauge_timeseries_ids",
    "save_gauge_timeseries", "delete_gauge_timeseries",
    "clear_property_timeseries", "clear_commercial_timeseries",
    "get_gauge_history", "iter_gauge_history_ids", "save_gauge_history",
    "delete_gauge_history",
    # storms / perils
    "get_storm_sequences", "storm_sequences_exists", "save_storm_sequences",
    "get_sequence_summary", "save_sequence_summary",
    "get_legacy_storm_sequences",
    "list_stress_storms", "get_stress_storm", "save_stress_storm",
    "get_stress_storm_index", "get_legacy_stress_storms",
    "list_sequence_gauges", "get_sequence_gauge", "save_sequence_gauge",
    "clear_sequence_gauges",
    "typhoon_events_exist", "get_typhoon_event", "iter_typhoon_event_ids",
    "save_typhoon_event",
    "get_fire_results", "save_fire_results", "get_seismic_results", "save_seismic_results",
    # trading
    "list_prs_trades", "iter_prs_trade_ids", "get_prs_trade", "commit_prs_trade",
    "save_prs_trade",
    "get_trade_marks", "save_trade_marks", "set_trade_status",
    "get_market_state", "save_market_state",
    "list_eod_snapshots", "iter_eod_snapshots", "get_eod_snapshot", "save_eod_snapshot",
    "delete_eod_snapshot", "clear_eod_snapshots",
    "get_hazard_curve_history", "save_hazard_curve_history",
    "get_trade_pnl_history", "save_trade_pnl_history",
    # classifiers
    "list_classifier_ids", "get_classifier", "save_classifier", "delete_classifier",
    "get_classifier_training_summary", "save_classifier_training_summary",
    "delete_classifier_training_summary",
    "get_classifier_timings", "save_classifier_timings", "delete_classifier_timings",
    # low-level document I/O (legacy loader layer)
    "read_json_document", "iter_document_names",
]
