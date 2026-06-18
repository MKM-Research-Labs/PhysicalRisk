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

"""Coverage tests for halong mortgage field generators — the InsuranceRate /
RecoveryHaircut decimal branches, the integer default branch and RLoanID."""

import random

import pytest

from port.rand.halong.mortgage import generators


@pytest.fixture(autouse=True)
def _seed():
    random.seed(20260614)


class TestHalongMortgageGeneratorsCoverage:
    def test_insurance_rate_decimal(self):
        v = generators.generate_decimal_value("InsuranceRate", {})  # line 93
        assert 0.0015 <= v <= 0.003

    def test_recovery_haircut_decimal(self):
        v = generators.generate_decimal_value("RecoveryHaircut", {})  # line 95
        assert 0.15 <= v <= 0.30

    def test_integer_unknown_field_default_branch(self):
        for _ in range(20):
            v = generators.generate_integer_value("UnknownIntField", {})  # line 150
            assert 1 <= v <= 10

    def test_text_rloan_id_uses_provided_id(self):
        assert generators.generate_text_value(
            "RLoanID", 0, {"mortgage_id": "RLOAN-X"}) == "RLOAN-X"  # line 175
        # falls back to a generated uuid when the id is absent
        v = generators.generate_text_value("RLoanID", 0, {})
        assert isinstance(v, str) and v
