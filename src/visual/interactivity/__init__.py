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
Interactivity modules for the visualization system.

Sub-modules:
- manager: InteractivityManager (unified coordinator)
- backend_handler: Backend communication
- context_menus: Context menu handler
- notifications: Notification system
- startup: Startup preloader
- gauge/: Gauge-level panels (gaugeha, gaugehc, gaugepdf, gaugesa)
- property/: Property panels (mortgagedetail, propertyhc, propertypdf, propertysa)
- storm/: Storm portfolio panel
- trading/: Trading desk panels
- governance/: Model governance panel
"""

from .backend_handler import BackendHandler  # noqa: F401
from .context_menus import ContextMenuHandler  # noqa: F401
from .gauge.gaugeha import GaugeGraphInteraction  # noqa: F401
from .gauge.gaugehc import GaugeHazardCurve  # noqa: F401
from .gauge.gaugepdf import GaugePDFPanel  # noqa: F401
from .gauge.gaugesa import GaugeStormAnalysis  # noqa: F401
from .governance.modelgovernance import ModelGovernancePanel  # noqa: F401
from .manager import InteractivityManager  # noqa: F401
from .notifications import (  # noqa: F401
    NotificationPosition,
    NotificationSystem,
    NotificationType,
    add_notifications_to_map,
    create_notification_system,
)
from .property.mortgagedetail import MortgageDetailPanel  # noqa: F401
from .property.propertyhc import PropertyHazardCurvePanel  # noqa: F401
from .property.propertypdf import PropertyPDFPanel  # noqa: F401
from .property.propertysa import PropertyStormAnalysis  # noqa: F401
from .startup import StartupPreloader  # noqa: F401
from .storm.stormportfolio import StormPortfolioPanel  # noqa: F401
from .trading.td_main_map import MainMapFS01  # noqa: F401
from .trading.tradingdesk import TradingDeskPanel  # noqa: F401

__all__ = [
    "StartupPreloader",
    "ContextMenuHandler",
    "BackendHandler",
    "GaugeGraphInteraction",
    "GaugeStormAnalysis",
    "GaugeHazardCurve",
    "PropertyStormAnalysis",
    "PropertyHazardCurvePanel",
    "GaugePDFPanel",
    "PropertyPDFPanel",
    "MortgageDetailPanel",
    "ModelGovernancePanel",
    "StormPortfolioPanel",
    "TradingDeskPanel",
    "MainMapFS01",
    "NotificationSystem",
    "NotificationType",
    "NotificationPosition",
    "InteractivityManager",
    "create_notification_system",
    "add_notifications_to_map",
]
