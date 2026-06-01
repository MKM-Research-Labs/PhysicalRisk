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
InteractivityManager — unified coordinator for all map interactivity components.
"""

import folium

from config import config

from .backend_handler import BackendHandler
from .context_menus import ContextMenuHandler
from .notifications import create_notification_system
from .startup import StartupPreloader

from .storm.stormportfolio import StormPortfolioPanel
from .gauge.gaugeha import GaugeGraphInteraction
from .gauge.gaugehc import GaugeHazardCurve
from .gauge.gaugepdf import GaugePDFPanel
from .gauge.gaugesa import GaugeStormAnalysis
from .property.loanpricer import LoanPricerPanel
from .property.rloandetail import RLoanDetailPanel
from .property.propertydetails import PropertyDetailsPanel
from .property.propertyhc import PropertyHazardCurvePanel
from .property.propertypdf import PropertyPDFPanel
from .property.propertysa import PropertyStormAnalysis
from .governance.modelgovernance import ModelGovernancePanel
from .trading.tradingdesk import TradingDeskPanel
from .trading.td_main_map import MainMapFS01


class InteractivityManager:
    """
    Unified manager for all map interactivity components.

    Coordinates context menus, backend communication, and notifications.
    """

    def __init__(self,
                 server_url: str = None,
                 notification_position: str = "top-right",
                 notification_timeout: int = 5000):
        self.startup_preloader = StartupPreloader()
        self.notifications = create_notification_system(
            position=notification_position,
            timeout=notification_timeout
        )
        self.backend = BackendHandler(server_url or config.SERVER_URL)
        self.context_menus = ContextMenuHandler()
        self.gauge_graph = GaugeGraphInteraction()
        self.gauge_storms = GaugeStormAnalysis()
        self.gauge_hazard = GaugeHazardCurve()
        self.property_storms = PropertyStormAnalysis()
        self.property_hazard = PropertyHazardCurvePanel()
        self.gauge_pdf = GaugePDFPanel()
        self.property_pdf = PropertyPDFPanel()
        self.property_details = PropertyDetailsPanel()
        self.rloan_detail = RLoanDetailPanel()
        self.loan_pricer = LoanPricerPanel()
        self.storm_portfolio = StormPortfolioPanel()
        self.model_governance = ModelGovernancePanel()
        self.trading_desk = TradingDeskPanel()
        self.main_map_fs01 = MainMapFS01()

    def setup_map_interactivity(self, folium_map) -> 'InteractivityManager':
        """Add all interactivity components to a map."""
        self.startup_preloader.add_to_map(folium_map)
        self.notifications.add_to_map(folium_map)
        self.backend.add_to_map(folium_map)
        self.gauge_graph.add_to_map(folium_map)
        self.gauge_storms.add_to_map(folium_map)
        self.gauge_hazard.add_to_map(folium_map)
        self.property_storms.add_to_map(folium_map)
        self.property_hazard.add_to_map(folium_map)
        self.gauge_pdf.add_to_map(folium_map)
        self.property_pdf.add_to_map(folium_map)
        self.property_details.add_to_map(folium_map)
        self.rloan_detail.add_to_map(folium_map)
        self.loan_pricer.add_to_map(folium_map)
        self.storm_portfolio.add_to_map(folium_map)
        self.model_governance.add_to_map(folium_map)
        self.trading_desk.add_to_map(folium_map)
        self.main_map_fs01.add_to_map(folium_map)
        self.context_menus.add_to_map(folium_map)

        copyright_html = """
        <div style="position:fixed;bottom:10px;right:10px;
             background:rgba(255,255,255,0.85);padding:4px 10px;
             border-radius:3px;font-size:11px;color:#555;
             box-shadow:0 1px 3px rgba(0,0,0,0.15);z-index:1000;
             font-family:Arial,sans-serif;">
            &copy; 2025-2026 MKM Research Labs
        </div>
        """
        folium_map.get_root().html.add_child(folium.Element(copyright_html))

        return self

    def configure(self, **kwargs) -> 'InteractivityManager':
        """Configure components."""
        if "server_url" in kwargs:
            self.backend.configure(server_url=kwargs["server_url"])

        if "notification_position" in kwargs or "notification_timeout" in kwargs:
            self.notifications.configure(
                position=kwargs.get("notification_position"),
                timeout=kwargs.get("notification_timeout")
            )

        if ("property_menu" in kwargs or "gauge_menu" in kwargs
                or "commercial_menu" in kwargs):
            self.context_menus.configure(
                property_menu=kwargs.get("property_menu"),
                gauge_menu=kwargs.get("gauge_menu"),
                commercial_menu=kwargs.get("commercial_menu"),
            )

        return self

    def get_statistics(self) -> dict:
        """Get statistics from all components."""
        return {
            "notifications": self.notifications.get_statistics(),
            "backend_handler": self.backend.get_statistics(),
            "context_menus": self.context_menus.get_statistics(),
        }
