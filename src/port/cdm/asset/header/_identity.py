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

"""Header identifiers and valuation sections of the asset header schema."""

HEADER = {
        "UPRN": {
            "type": "string",
            "description": "Unique Property Reference Number"
        },
        "PropertyID": {
            "type": "string",
            "description": "Unique identifier for the property"
        },
        "CatchmentID": {
            "type": "string",
            "description": "Identifier for the river catchment (e.g., 'thames', 'rhine')"
        },
        "propertyType": {
            "type": "menu",
            "options": ["residential", "commercial", "industrial"],
            "description": "Basic property type classification"
        },
        "propertyStatus": {
            "type": "menu",
            "options": ["active", "inactive", "under_construction"],
            "description": "Current status of property"
        }
}

VALUATION = {
        "PropertyValue": {
            "type": "decimal",
            "description": "Current market value of the property"
        },
        "ValuationDate": {
            "type": "date",
            "description": "Date of last valuation"
        },
        "ValuationMethod": {
            "type": "menu",
            "options": ["Market comparison", "Income approach", "Cost approach", "Automated valuation"],
            "description": "Method used for valuation"
        }
}
