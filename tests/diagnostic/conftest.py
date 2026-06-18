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
Shared fixtures for flood propagation diagnostic tests.
"""

import json
from pathlib import Path

import pytest

from config import PortfolioConfig

DATA_DIR = Path(PortfolioConfig().get_input_dir())


def _load_json(path):
    with open(path) as f:
        return json.load(f)


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------

@pytest.fixture(scope="module")
def gauge_json():
    return _load_json(DATA_DIR / 'gauge.json')


@pytest.fixture(scope="module")
def gaugets():
    result = {}
    gaugets_dir = DATA_DIR / 'gaugets'
    for f in gaugets_dir.glob('*.json'):
        data = _load_json(f)
        result[f.stem] = data
    return result


@pytest.fixture(scope="module")
def properties():
    result = {}
    pts_dir = DATA_DIR / 'propertyts'
    for f in pts_dir.glob('PROP-*.json'):
        data = _load_json(f)
        result[data['property_id']] = data
    return result


@pytest.fixture(scope="module")
def gaugehc():
    return _load_json(DATA_DIR / 'gaugehc.json')
