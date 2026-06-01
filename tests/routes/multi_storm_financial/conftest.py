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

"""Shared fixtures and helpers for multi-storm financial tests (MKM-SS-001)."""

import json


def _prop_flood_file(pts_dir, prop_id, flood_events):
    """Write a propertyts file for one property."""
    data = {"property_id": prop_id, "flood_events": flood_events}
    (pts_dir / f"{prop_id}.json").write_text(json.dumps(data))


def _property_json(path, properties):
    """Write property.json with valuation data."""
    records = [
        {
            "PropertyHeader": {
                "Header": {"PropertyID": pid},
                "Valuation": {"PropertyValue": value},
            }
        }
        for pid, value in properties
    ]
    path.write_text(json.dumps({"properties": records}))


def _mortgage_json(path, mortgages):
    """Write loan.json with outstanding balance data."""
    records = [
        {
            "RLoan": {
                "Header": {"RLoanID": f"MORT-{pid}", "PropertyID": pid},
                "CurrentStatus": {
                    "OutstandingBalance": balance,
                    "CurrentLTV": round(balance / value, 2),
                    "RemainingTerm": 240,
                },
            }
        }
        for pid, balance, value in mortgages
    ]
    path.write_text(json.dumps({"loans": records}))


def make_test_client(tmp_path, monkeypatch, pts_setup_fn):
    """Create a Flask test client with monkeypatched config paths.

    pts_setup_fn(pts_dir) is called to populate the propertyts directory.
    """
    from config import config

    pts_dir = tmp_path / "propertyts"
    pts_dir.mkdir()
    pts_setup_fn(pts_dir)

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_input_path", lambda name: tmp_path / name)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: tmp_path / "gaugets")

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()
