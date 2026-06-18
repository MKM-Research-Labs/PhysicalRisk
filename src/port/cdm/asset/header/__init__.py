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
Asset header schema — identifiers, valuation, attributes, construction, location.

Carries the full PropertyHeader schema as it existed in the legacy
property/schema/header.py. The residential/commercial split (e.g.
moving NumberBedrooms/CouncilTaxBand into asset/residential/header.py)
will happen on a later pass — this file is currently asset-wide so
the legacy property pipeline keeps emitting byte-identical JSON.
"""

from ._attributes import PROPERTY_ATTRIBUTES
from ._construction import CONSTRUCTION
from ._identity import HEADER, VALUATION
from ._location import LOCATION

HEADER_SCHEMA = {
    "Header": HEADER,
    "Valuation": VALUATION,
    "PropertyAttributes": PROPERTY_ATTRIBUTES,
    "Construction": CONSTRUCTION,
    "Location": LOCATION,
}
