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
Rhine catchment definition for the Rhine River, Germany/Netherlands.

STUB: This catchment is awaiting gauge point and area data.
The Rhine is one of Europe's major rivers with significant flood risk
exposure in Cologne, Düsseldorf, and Rotterdam.
"""

from .base import BaseCatchment


class RhineCatchment(BaseCatchment):
    """
    Rhine River catchment covering Germany and Netherlands.
    
    STUB: Gauge points and area data to be added when available.
    
    The Rhine has very high industrial and urban asset concentration,
    making it one of Europe's highest property-value-at-risk catchments.
    """
    
    NAME = "rhine"
    REGION = "Europe"
    DISPLAYNAME = "Rhine"
    COUNTRY = "Germany/Netherlands"
    
    # TODO: Add gauge points when data available
    # Format: (lat, lon, elevation_meters)
    GAUGEPOINTS = []
    
    # TODO: Add area names along the river
    AREAS = []
    
    # TODO: Add street names by area
    STREETS = {}
    
    # TODO: Add property value factors by area
    AREAVALUEFACTORS = {}
