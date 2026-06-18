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

"""Shared section renderers for asset reports.

The asset CDM (src/port/cdm/asset/) splits asset records into three
buckets: sections shared by all asset types (Header, Valuation,
Construction, Location, RiskAssessment, EnergyPerformance,
ProtectionMeasures, HistoryAndIncidents, TransactionHistory),
residential-only sections (PropertyAttributes, Contents), and
commercial-only sections (CommercialAttributes, AccessibilityFeatures,
Tenancy).

This package mirrors the *shared* leg: one ``render_<section>``
function per shared section, taking a section dict + a page-style
context and returning ReportLab flowables. Each render function is
catchment- and asset-type-agnostic — the caller (property or
commercial report generator) is responsible for unwrapping the right
CDM path before calling.
"""

from .base import AssetBasePage
from .construction import render_construction
from .energy import render_energy
from .header import render_header
from .history import render_history
from .location import render_location
from .protection import render_protection
from .risk_assessment import render_risk_assessment
from .transactions import render_transactions
from .valuation import render_valuation

__all__ = [
    "AssetBasePage",
    "render_construction",
    "render_energy",
    "render_header",
    "render_history",
    "render_location",
    "render_protection",
    "render_risk_assessment",
    "render_transactions",
    "render_valuation",
]
