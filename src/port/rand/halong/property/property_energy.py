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
Energy calculation methods for Thames property random data.

Carbon emissions, energy consumption, grid electricity, gas, solar, energy bills.
"""

import random
from typing import Any, Dict


def calculate_carbon_emissions(location_info: Dict[str, Any]) -> float:
    """Calculate annual carbon emissions based on property characteristics."""
    area = location_info.get('property_area', 100)
    base_emissions = area * random.uniform(25, 80)
    return round(base_emissions, 1)


def calculate_annual_energy(location_info: Dict[str, Any]) -> float:
    """Calculate total annual energy consumption."""
    area = location_info.get('property_area', 100)
    base_consumption = area * random.uniform(120, 250)
    return round(base_consumption, 0)


def calculate_grid_electricity(location_info: Dict[str, Any]) -> float:
    """Calculate grid electricity usage."""
    total_energy = location_info.get('annual_energy', 15000)
    electricity_proportion = random.uniform(0.3, 0.8)
    return round(total_energy * electricity_proportion, 0)


def calculate_gas_usage(location_info: Dict[str, Any]) -> float:
    """Calculate gas usage."""
    total_energy = location_info.get('annual_energy', 15000)
    grid_electricity = location_info.get('grid_electricity', 6000)
    remaining = total_energy - grid_electricity
    return max(0, round(remaining * random.uniform(0.6, 1.0), 0))


def calculate_solar_generation(location_info: Dict[str, Any]) -> float:
    """Calculate solar generation if renewable system present."""
    renewable_system = location_info.get('renewable_system', 'None')
    if renewable_system in ['Solar PV', 'Multiple']:
        area = location_info.get('property_area', 100)
        solar_capacity = area * random.uniform(0.1, 0.3) * 150
        return round(solar_capacity, 0)
    return 0


def calculate_energy_bill(location_info: Dict[str, Any]) -> float:
    """Calculate annual energy bill."""
    grid_electricity = location_info.get('grid_electricity', 6000)
    gas_usage = location_info.get('gas_usage', 9000)

    electricity_rate = 0.30  # GBP/kWh
    gas_rate = 0.07  # GBP/kWh

    bill = (grid_electricity * electricity_rate) + (gas_usage * gas_rate)
    return round(bill, 2)
