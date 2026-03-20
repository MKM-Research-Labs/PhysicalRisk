#!/usr/bin/env python3

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
        'mortgage_report', 'gauge_history', 'health_check',
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
