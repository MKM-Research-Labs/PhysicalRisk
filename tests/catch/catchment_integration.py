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
Simple test to verify catchment selector is working.
"""

def test_routes():
    """Test that routes register correctly."""
    print("Testing route registration...")

    from flask import Flask

    from routes import register_blueprints

    app = Flask(__name__)
    register_blueprints(app)

    # Check for catchment routes
    catchment_routes = [
        rule for rule in app.url_map.iter_rules()
        if 'catchment' in rule.rule or 'select' in rule.rule
    ]

    if catchment_routes:
        print(f"✅ Found {len(catchment_routes)} catchment route(s)")
        for rule in catchment_routes:
            methods = list(rule.methods - {'HEAD', 'OPTIONS'})
            print(f"   {methods} {rule.rule}")
        return True
    else:
        print("❌ No catchment routes found")
        return False

def test_html_file():
    """Test that select_catchment.html exists."""
    from pathlib import Path

    print("\nTesting HTML file...")
    html_path = Path(__file__).parent / 'select_catchment.html'

    if html_path.exists():
        size = html_path.stat().st_size
        print(f"✅ select_catchment.html exists ({size} bytes)")
        return True
    else:
        print(f"❌ select_catchment.html not found at {html_path}")
        return False

def test_config():
    """Test that config has CATCHMENT attribute."""
    print("\nTesting config...")

    from config import config

    if hasattr(config, 'CATCHMENT'):
        print(f"✅ config.CATCHMENT = {config.CATCHMENT}")
        return True
    else:
        print("❌ config.CATCHMENT not found")
        return False


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

if __name__ == '__main__':
    print("=" * 60)
    print("  Catchment Selector Integration Test")
    print("=" * 60)
    print()

    results = []
    results.append(test_routes())
    results.append(test_html_file())
    results.append(test_config())

    print()
    print("=" * 60)
    if all(results):
        print("  ✅ ALL TESTS PASSED")
        print()
        print("  Ready to run:")
        print("    python server.py")
        print()
        print("  Then visit:")
        print("    http://127.0.0.1:5013/select-catchment")
    else:
        print("  ❌ SOME TESTS FAILED")
    print("=" * 60)
