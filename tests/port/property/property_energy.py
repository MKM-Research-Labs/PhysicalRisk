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
Tests for port.rand.thames.property.property_energy — energy calculations.

Covers: calculate_carbon_emissions, calculate_annual_energy,
calculate_grid_electricity, calculate_gas_usage,
calculate_solar_generation (with/without solar), calculate_energy_bill.
"""

import pytest

from port.rand.thames.property.property_energy import (
    calculate_carbon_emissions,
    calculate_annual_energy,
    calculate_grid_electricity,
    calculate_gas_usage,
    calculate_solar_generation,
    calculate_energy_bill,
)


# ===========================================================================
# calculate_carbon_emissions
# ===========================================================================

class TestCalculateCarbonEmissions:

    def test_returns_positive_value(self):
        result = calculate_carbon_emissions({"property_area": 100})
        assert result > 0

    def test_uses_default_area_when_missing(self):
        result = calculate_carbon_emissions({})
        assert result > 0

    def test_larger_area_tends_to_give_larger_emissions(self):
        # Run several times to reduce random fluke chance
        small = [calculate_carbon_emissions({"property_area": 50}) for _ in range(5)]
        large = [calculate_carbon_emissions({"property_area": 300}) for _ in range(5)]
        assert sum(large) > sum(small)

    def test_is_float(self):
        result = calculate_carbon_emissions({"property_area": 80})
        assert isinstance(result, float)


# ===========================================================================
# calculate_annual_energy
# ===========================================================================

class TestCalculateAnnualEnergy:

    def test_returns_positive_value(self):
        result = calculate_annual_energy({"property_area": 100})
        assert result > 0

    def test_uses_default_area_when_missing(self):
        result = calculate_annual_energy({})
        assert result > 0

    def test_larger_area_gives_larger_energy(self):
        small = [calculate_annual_energy({"property_area": 50}) for _ in range(5)]
        large = [calculate_annual_energy({"property_area": 300}) for _ in range(5)]
        assert sum(large) > sum(small)


# ===========================================================================
# calculate_grid_electricity
# ===========================================================================

class TestCalculateGridElectricity:

    def test_returns_positive_value(self):
        result = calculate_grid_electricity({"annual_energy": 15000})
        assert result >= 0

    def test_uses_default_energy_when_missing(self):
        result = calculate_grid_electricity({})
        assert result > 0

    def test_fraction_of_total(self):
        # Grid electricity should be 30-80% of annual_energy = 15000
        results = [calculate_grid_electricity({"annual_energy": 15000}) for _ in range(20)]
        assert all(4500 <= r <= 12001 for r in results)


# ===========================================================================
# calculate_gas_usage
# ===========================================================================

class TestCalculateGasUsage:

    def test_returns_non_negative(self):
        result = calculate_gas_usage({"annual_energy": 15000, "grid_electricity": 6000})
        assert result >= 0

    def test_uses_defaults_when_missing(self):
        result = calculate_gas_usage({})
        assert result >= 0

    def test_less_than_remaining_energy(self):
        # gas <= (annual - electricity)
        result = calculate_gas_usage({"annual_energy": 15000, "grid_electricity": 6000})
        assert result <= 9001  # remaining = 9000, gas <= 100% of remaining

    def test_no_negative_when_electricity_exceeds_total(self):
        # Edge case: electricity > total → remaining = 0 → gas = 0
        result = calculate_gas_usage({"annual_energy": 5000, "grid_electricity": 8000})
        assert result == 0


# ===========================================================================
# calculate_solar_generation
# ===========================================================================

class TestCalculateSolarGeneration:

    def test_no_solar_returns_zero(self):
        result = calculate_solar_generation({"renewable_system": "None"})
        assert result == 0

    def test_no_system_returns_zero(self):
        result = calculate_solar_generation({})
        assert result == 0

    def test_solar_pv_returns_positive(self):
        result = calculate_solar_generation({
            "renewable_system": "Solar PV",
            "property_area": 100,
        })
        assert result > 0

    def test_multiple_returns_positive(self):
        result = calculate_solar_generation({
            "renewable_system": "Multiple",
            "property_area": 100,
        })
        assert result > 0

    def test_heat_pump_returns_zero(self):
        result = calculate_solar_generation({"renewable_system": "Heat Pump"})
        assert result == 0

    def test_solar_uses_default_area_when_missing(self):
        result = calculate_solar_generation({"renewable_system": "Solar PV"})
        assert result > 0


# ===========================================================================
# calculate_energy_bill
# ===========================================================================

class TestCalculateEnergyBill:

    def test_returns_positive_value(self):
        result = calculate_energy_bill({"grid_electricity": 6000, "gas_usage": 9000})
        assert result > 0

    def test_correct_calculation(self):
        # electricity: 6000 * 0.30 = 1800, gas: 9000 * 0.07 = 630 → 2430
        result = calculate_energy_bill({"grid_electricity": 6000, "gas_usage": 9000})
        assert abs(result - 2430.0) < 0.01

    def test_uses_defaults_when_missing(self):
        result = calculate_energy_bill({})
        # Default: 6000 electricity, 9000 gas → 2430
        assert abs(result - 2430.0) < 0.01

    def test_zero_usage_returns_zero(self):
        result = calculate_energy_bill({"grid_electricity": 0, "gas_usage": 0})
        assert result == 0.0

    def test_is_float(self):
        result = calculate_energy_bill({"grid_electricity": 5000, "gas_usage": 8000})
        assert isinstance(result, float)
