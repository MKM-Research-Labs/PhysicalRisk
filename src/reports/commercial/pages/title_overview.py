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

"""Title / overview page for a commercial asset."""

from datetime import datetime
from typing import Any, Dict, List

from reportlab.platypus import Paragraph, Spacer

from reports.asset._helpers import build_kv_table

from ..base import CommercialBasePage


class TitleOverviewPage(CommercialBasePage):
    """Front cover page: title, building/address summary, key attributes."""

    def generate_elements(self, commercial_data: Dict[str, Any], **kwargs) -> List:
        asset = commercial_data.get("CommercialAsset", {}) or {}
        header = asset.get("Header", {}) or {}
        location = asset.get("Location", {}) or {}
        attrs = asset.get("CommercialAttributes", {}) or {}
        valuation = asset.get("Valuation", {}) or {}

        elements: List = []

        # --- Title block ---
        building_name = (
            location.get("BuildingName")
            or location.get("StreetName")
            or header.get("PropertyID")
            or "Commercial Asset"
        )
        elements.append(Paragraph("Commercial Asset Report",
                                  self.styles["Title"]))
        elements.append(Paragraph(str(building_name),
                                  self.styles["SubTitle"]))
        elements.append(Spacer(1, self.spacing["major_section"]))

        # --- Headline figures ---
        from config import config
        currency_symbol = {"thames": "£", "halong": "$"}.get(
            config.catchment_id, "£"
        )

        full_address = ", ".join(
            str(v) for v in (
                location.get("BuildingNumber"),
                location.get("StreetName"),
                location.get("TownCity"),
                location.get("Postcode"),
            ) if v
        ) or "Address unknown"

        value = valuation.get("PropertyValue")
        rows = [
            ("Property ID",       header.get("PropertyID")),
            ("Catchment",         header.get("CatchmentID")),
            ("Commercial Type",   attrs.get("CommercialType")),
            ("Use Class (UKO)",   attrs.get("UseClassUKO")),
            ("Address",           full_address),
            ("Floor Area (sqm)",  attrs.get("PropertyAreaSqm")),
            ("Storeys",           attrs.get("NumberOfStoreys")),
            ("Year of Construction", attrs.get("ConstructionYear")),
            ("Valuation",         self._format_currency(value, currency_symbol)
                                  if isinstance(value, (int, float)) else None),
            ("Report Generated",  datetime.now().strftime("%Y-%m-%d %H:%M")),
        ]
        elements.extend(build_kv_table(
            rows, self,
            header=("Field", "Value"),
            style="standard",
        ))
        return elements
