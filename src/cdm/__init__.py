# Copyright (c) 2025 MKM Research Labs. All rights reserved.
# 
# This software is provided under license by MKM Research Labs. 
# Use, reproduction, distribution, or modification of this code is subject to the 
# terms and conditions of the license agreement provided with this software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Common Data Model (CDM) Package.

This package contains standardized data models for various entities used in the project.
CDM classes provide schema definitions and transformation methods to ensure data consistency.
"""

from .flood_gauge_cdm import FloodGaugeCDM
from .mortgage_cdm import MortgageCDM
from .property_cdm import PropertyCDM
from .tc_event_cdm import TCEventCDM
from .tc_event_ts_cdm import TCEventTSCDM

__all__ = [
    'FloodGaugeCDM',
    'MortgageCDM',
    'PropertyCDM',
    'TCEventCDM',
    'TCEventTSCDM'
]