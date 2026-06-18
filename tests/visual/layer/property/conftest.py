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

"""Shared helpers for property layer popup tests."""


def make_property_info(property_id="PROP-001", lat=51.5, lon=-0.1,
                       river_dist=200, ground_elevation=3.5):
    return {
        "property_id": property_id,
        "coordinates": {"latitude": lat, "longitude": lon},
        "address": {
            "street": "Main St",
            "city": "London",
            "postcode": "EC1A 1BB",
            "post_code": "EC1A 1BB",
        },
        "valuation": {"current_value": 500_000},
        "ground_elevation": ground_elevation,
        "floor_level_m": 0.5,
        "flood_zone": "2",
        "river_distance_m": river_dist,
        "property_type": "Detached",
        "building_type": "House",
        "construction_type": "Brick",
        "construction_year": 2000,
        "number_of_storeys": 2,
    }


def make_mortgage_info(loan=250_000, rate=0.04, term=25, provider="Test Bank", ltv=None):
    info = {
        "original_loan": loan,
        "original_lending_rate": rate,
        "term_years": term,
        "mortgage_provider": provider,
    }
    if ltv is not None:
        info["loan_to_value_ratio"] = ltv
    return info
