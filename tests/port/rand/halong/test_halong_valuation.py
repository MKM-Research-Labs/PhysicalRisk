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

"""Branch coverage for the halong property_valuation module (byte-identical
copy of thames). Exercises the None-fallback branches and the random
market/condition branches by calling each function repeatedly with minimal
location_info and varied seeds."""

import random

import pytest

from port.rand.halong.property import property_valuation as v


def test_property_area_default_type():
    random.seed(1)
    area = v.calculate_property_area({})  # unknown type → default range
    assert area > 0


def test_property_value_computes_area_when_missing():
    random.seed(2)
    info = {"property_type": "Flat"}  # no property_area → 78-79 fill it in
    val = v.calculate_property_value(info)
    assert val > 0
    assert "property_area" in info  # side-effect populated


def test_sale_price_computes_value_when_missing():
    random.seed(3)
    # no property_value → 139 calls calculate_property_value
    price = v.calculate_sale_price({"property_type": "Flat"})
    assert price >= 50000


def test_sale_price_with_valid_sale_date():
    random.seed(4)
    price = v.calculate_sale_price({
        "property_value": 300000, "sale_date": "2025-01-01"})
    assert price >= 50000


def test_sale_price_with_bad_sale_date():
    random.seed(5)
    # unparseable date → 146-147 except branch
    price = v.calculate_sale_price({
        "property_value": 300000, "sale_date": "not-a-date"})
    assert price >= 50000


def test_sale_price_covers_all_year_and_market_branches():
    # Sweep seeds so years_ago<1, <2, >=2 and boom/normal/recession all hit.
    for seed in range(60):
        random.seed(seed)
        price = v.calculate_sale_price({"property_value": 300000})
        assert 50000 <= price <= 8000000


def test_monthly_rent_computes_value_and_area_when_missing():
    random.seed(6)
    # no property_value and no property_area → 181 + 184 branches
    rent = v.calculate_monthly_rent({"property_type": "Flat"})
    assert 800 <= rent <= 15000


def test_monthly_rent_covers_furnished_branch():
    for seed in range(40):
        random.seed(seed)
        rent = v.calculate_monthly_rent({
            "property_value": 300000, "property_area": 80})
        assert 800 <= rent <= 15000


def test_insurance_premium_computes_value_and_area_when_missing():
    random.seed(7)
    # 229 + 232 None branches
    prem = v.calculate_insurance_premium({"property_type": "Flat"})
    assert prem > 0


def test_insurance_premium_covers_security_and_claims_branches():
    for seed in range(60):
        random.seed(seed)
        prem = v.calculate_insurance_premium({
            "property_value": 300000, "property_area": 80})
        assert prem > 0
