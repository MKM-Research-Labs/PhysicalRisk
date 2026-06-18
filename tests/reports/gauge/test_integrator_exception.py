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
Tests for missing coverage in reports.gauge.gauge_integrator.

Covers:
- Lines 161-163: exception in generate_report_for_gauge returns None
- Lines 199-201: exception in validate_gauge_exists returns False
- Lines 236-238: exception in get_available_gauges returns []
"""

import json
from pathlib import Path

import pytest


class TestGenerateReportForGaugeException:
    """Lines 161-163: exception during report generation returns None."""

    def test_corrupt_json_returns_none(self, tmp_path):
        from reports.gauge.gauge_integrator import generate_report_for_gauge
        gauge_file = tmp_path / "gauge.json"
        gauge_file.write_text("{corrupt json!!!")
        result = generate_report_for_gauge(
            "GAUGE-001", gauge_file, tmp_path / "output"
        )
        assert result is None

    def test_non_json_file_returns_none(self, tmp_path):
        from reports.gauge.gauge_integrator import generate_report_for_gauge
        gauge_file = tmp_path / "gauge.json"
        gauge_file.write_bytes(b"\x00\x01\x02")  # binary nonsense
        result = generate_report_for_gauge(
            "GAUGE-001", gauge_file, tmp_path / "output"
        )
        assert result is None


class TestValidateGaugeExistsException:
    """Lines 199-201: exception in validate_gauge_exists returns False."""

    def test_corrupt_json_returns_false(self, tmp_path):
        from reports.gauge.gauge_integrator import validate_gauge_exists
        gauge_file = tmp_path / "gauge.json"
        gauge_file.write_text("not valid json")
        result = validate_gauge_exists("GAUGE-001", gauge_file)
        assert result is False

    def test_binary_file_returns_false(self, tmp_path):
        from reports.gauge.gauge_integrator import validate_gauge_exists
        gauge_file = tmp_path / "gauge.json"
        gauge_file.write_bytes(b"\xff\xfe")
        result = validate_gauge_exists("GAUGE-001", gauge_file)
        assert result is False


class TestGetAvailableGaugesException:
    """Lines 236-238: exception in get_available_gauges returns []."""

    def test_corrupt_json_returns_empty(self, tmp_path):
        from reports.gauge.gauge_integrator import get_available_gauges
        gauge_file = tmp_path / "gauge.json"
        gauge_file.write_text("{bad json")
        result = get_available_gauges(gauge_file)
        assert result == []

    def test_binary_file_returns_empty(self, tmp_path):
        from reports.gauge.gauge_integrator import get_available_gauges
        gauge_file = tmp_path / "gauge.json"
        gauge_file.write_bytes(b"\x00\x01")
        result = get_available_gauges(gauge_file)
        assert result == []
