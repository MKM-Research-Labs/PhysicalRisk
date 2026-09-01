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
Interactivity modules for the visualization system.

Sub-modules:
- manager: InteractivityManager (unified coordinator)
- backend_handler: Backend communication
- context_menus: Context menu handler
- notifications: Notification system
- startup: Startup preloader
- gauge/: Gauge-level panels (gaugeha, gaugehc, gaugepdf, gaugesa)
- property/: Property panels (rloandetail, propertyhc, propertypdf, propertysa)
- storm/: Storm portfolio panel
- trading/: Trading desk panels
"""

from .manager import InteractivityManager  # noqa: F401

from .backend_handler import BackendHandler  # noqa: F401
from .context_menus import ContextMenuHandler  # noqa: F401
from .notifications import (  # noqa: F401
    NotificationPosition,
    NotificationSystem,
    NotificationType,
    add_notifications_to_map,
    create_notification_system,
)
from .startup import StartupPreloader  # noqa: F401

from .storm.stormportfolio import StormPortfolioPanel  # noqa: F401
from .gauge.gaugeha import GaugeGraphInteraction  # noqa: F401
from .gauge.gaugehc import GaugeHazardCurve  # noqa: F401
from .gauge.gaugepdf import GaugePDFPanel  # noqa: F401
from .gauge.gaugesa import GaugeStormAnalysis  # noqa: F401
from .property.rloandetail import RLoanDetailPanel  # noqa: F401
from .property.propertyhc import PropertyHazardCurvePanel  # noqa: F401
from .property.propertypdf import PropertyPDFPanel  # noqa: F401
from .property.propertysa import PropertyStormAnalysis  # noqa: F401
from .trading.tradingdesk import TradingDeskPanel  # noqa: F401
from .trading.td_main_map import MainMapFS01  # noqa: F401

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
    "RLoanDetailPanel",
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
