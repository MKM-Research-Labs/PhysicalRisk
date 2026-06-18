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

"""Branch coverage for the per-type helper functions in the halong commercial
generators module (byte-identical copy of thames). Drives the Retail /
Hotel / MixedUse / MultiFamily branches of each helper directly."""

import random

import pytest

from port.rand.halong.commercial.commercial_random import generators as g


@pytest.fixture(autouse=True)
def _halong(monkeypatch):
    """Activate the halong profile (BRI enabled) for the shared generators."""
    from config import config
    monkeypatch.setattr(config, "_catchment_id", "halong")


def test_bri_builds_prototype_when_absent():
    # bri_prototype missing → _bri calls for_commercial (line 29).
    proto = g._bri({"commercial_type": "Office"})
    assert isinstance(proto, dict)


def test_bri_uses_existing_prototype():
    sentinel = {"wind_codes": []}
    assert g._bri({"bri_prototype": sentinel}) is sentinel


def test_bri_defaults_mixeduse_when_type_none():
    proto = g._bri({"commercial_type": None})
    assert isinstance(proto, dict)


@pytest.mark.parametrize("ctype", ["Retail", "MixedUse", "Office"])
def test_service_core_branches(ctype):
    random.seed(1)
    vals = {g._service_core({"commercial_type": ctype}) for _ in range(30)}
    assert vals  # all branches produce valid strings
    assert all(isinstance(v, str) for v in vals)


@pytest.mark.parametrize("ctype", ["Retail", "Hotel", "MixedUse", "Office"])
def test_goods_lift_count_branches(ctype):
    random.seed(2)
    vals = {g._goods_lift_count({"commercial_type": ctype}) for _ in range(30)}
    assert all(isinstance(v, int) and v >= 0 for v in vals)


@pytest.mark.parametrize("ctype", ["MultiFamily", "MixedUse", "Hotel", "Office"])
def test_covenant_strength_branches(ctype):
    random.seed(3)
    vals = {g._covenant_strength({"commercial_type": ctype}) for _ in range(30)}
    assert all(isinstance(v, str) for v in vals)


def test_grade_to_rating():
    assert g._grade_to_rating(None) == "N/A"
    assert g._grade_to_rating("N/A") == "N/A"
    assert g._grade_to_rating("A") == "A"
