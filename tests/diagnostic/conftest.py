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
