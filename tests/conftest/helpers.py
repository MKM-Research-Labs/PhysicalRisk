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

"""Assertion helpers and file creation utilities for tests."""

import json
from pathlib import Path
from typing import Any, Dict


def create_test_file(directory: Path, filename: str, data: Any) -> Path:
    """Create a test data file containing JSON-encoded data."""
    filepath = directory / filename
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    return filepath


def assert_valid_property(data: Dict[str, Any]) -> None:
    """Assert that data matches property CDM structure."""
    assert 'PropertyHeader' in data
    assert 'Header' in data['PropertyHeader']
    assert 'PropertyID' in data['PropertyHeader']['Header']


def assert_valid_gauge(data: Dict[str, Any]) -> None:
    """Assert that data matches gauge CDM structure."""
    assert 'FloodGauge' in data
    assert 'Header' in data['FloodGauge']
    assert 'GaugeID' in data['FloodGauge']['Header']


def assert_valid_mortgage(data: Dict[str, Any]) -> None:
    """Assert that data matches mortgage structure."""
    assert 'MortgageID' in data
    assert 'PropertyID' in data
