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
