#!/usr/bin/env python3

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
Catchment configuration integration tests.

Previously also covered the /select-catchment selector page and its
/api/set-catchment endpoint; both were removed as legacy (the active
catchment is fixed by the CLI flag at server start, so there is no
in-app selection step). What remains here is catchment-related config.
"""

def test_config():
    """Test that config exposes the active CATCHMENT."""
    from config import config

    assert hasattr(config, 'CATCHMENT'), "config.CATCHMENT not found"
    assert config.CATCHMENT, "config.CATCHMENT is empty"


def test_config_endpoints_include_health_check():
    """Test that config ENDPOINTS includes health_check for backend handler."""
    from config import PortfolioConfig

    cfg = PortfolioConfig()
    required_endpoints = [
        'properties', 'gauges', 'property_report', 'gauge_report',
        'rloan_report', 'gauge_history', 'health_check',
    ]
    for ep in required_endpoints:
        assert ep in cfg.ENDPOINTS, f"Missing required endpoint: {ep}"
    assert cfg.ENDPOINTS['health_check'] == '/api/v1/health'
