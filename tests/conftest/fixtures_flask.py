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

"""Fixtures for Flask test app and client instances."""

import pytest

from fixtures_admin import AuthenticatedTestClient


@pytest.fixture
def flask_app(populated_data_dir, monkeypatch):
    """Create a Flask test app with mocked config."""
    from config import config
    monkeypatch.setattr(config, 'get_input_dir', lambda: populated_data_dir)
    monkeypatch.setattr(config, 'get_reports_dir', lambda: populated_data_dir / 'reports')

    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.test_client_class = AuthenticatedTestClient
    return app


@pytest.fixture
def full_flask_app(fully_populated_data_dir, monkeypatch):
    """Create a Flask test app with ALL data types (propertyts, propertyhc, gaugehc)."""
    from config import config
    monkeypatch.setattr(config, 'get_input_dir', lambda: fully_populated_data_dir)
    monkeypatch.setattr(config, 'get_input_path',
                        lambda filename: fully_populated_data_dir / filename)
    monkeypatch.setattr(config, 'get_gaugets_dir', lambda: fully_populated_data_dir / 'gaugets')
    monkeypatch.setattr(config, 'get_gaugehd_dir', lambda: fully_populated_data_dir / 'gaugehd')
    monkeypatch.setattr(config, 'get_reports_dir', lambda: fully_populated_data_dir / 'reports')
    monkeypatch.setattr(config, 'get_gauge_reports_dir',
                        lambda: fully_populated_data_dir / 'reports' / 'gauge')

    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.test_client_class = AuthenticatedTestClient
    return app


@pytest.fixture
def full_client(full_flask_app):
    """Flask test client with all data types available."""
    return full_flask_app.test_client()


@pytest.fixture
def client(flask_app):
    """Create a Flask test client."""
    return flask_app.test_client()
