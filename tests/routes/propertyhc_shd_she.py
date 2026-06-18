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
Tests for synthetic hazard distance (SHD) and elevation (SHE) routes.

Covers:
  GET /api/v1/propertyshd/summary
  GET /api/v1/propertyshe/summary
  GET /api/v1/properties/<prop_id>/shd
  GET /api/v1/properties/<prop_id>/she
"""


# ---------------------------------------------------------------------------
# GET /api/v1/propertyshd/summary
# ---------------------------------------------------------------------------

class TestPropertyshdSummary:

    def test_no_data_returns_404(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/propertyshd/summary")
        assert r.status_code == 404

    def test_no_data_status_error(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/propertyshd/summary")
        assert r.get_json()["status"] == "error"

    def test_options_returns_200(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/propertyshd/summary")
        assert r.status_code == 200

    def test_options_status_ok(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/propertyshd/summary")
        assert r.get_json()["status"] == "ok"

    def test_returns_200_with_data(self, shd_env):
        r = shd_env.get("/api/v1/propertyshd/summary")
        assert r.status_code == 200

    def test_status_is_success(self, shd_env):
        r = shd_env.get("/api/v1/propertyshd/summary")
        assert r.get_json()["status"] == "success"

    def test_response_has_metadata(self, shd_env):
        r = shd_env.get("/api/v1/propertyshd/summary")
        assert "metadata" in r.get_json()["data"]

    def test_response_has_summary(self, shd_env):
        r = shd_env.get("/api/v1/propertyshd/summary")
        assert "summary" in r.get_json()["data"]


# ---------------------------------------------------------------------------
# GET /api/v1/propertyshe/summary
# ---------------------------------------------------------------------------

class TestPropertysheSummary:

    def test_no_data_returns_404(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/propertyshe/summary")
        assert r.status_code == 404

    def test_no_data_status_error(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/propertyshe/summary")
        assert r.get_json()["status"] == "error"

    def test_options_returns_200(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/propertyshe/summary")
        assert r.status_code == 200

    def test_options_status_ok(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/propertyshe/summary")
        assert r.get_json()["status"] == "ok"

    def test_returns_200_with_data(self, she_env):
        r = she_env.get("/api/v1/propertyshe/summary")
        assert r.status_code == 200

    def test_status_is_success(self, she_env):
        r = she_env.get("/api/v1/propertyshe/summary")
        assert r.get_json()["status"] == "success"

    def test_response_has_metadata(self, she_env):
        r = she_env.get("/api/v1/propertyshe/summary")
        assert "metadata" in r.get_json()["data"]

    def test_response_has_summary(self, she_env):
        r = she_env.get("/api/v1/propertyshe/summary")
        assert "summary" in r.get_json()["data"]


# ---------------------------------------------------------------------------
# GET /api/v1/properties/<prop_id>/shd
# ---------------------------------------------------------------------------

class TestPropertyShd:

    def test_no_data_returns_404(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/properties/PROP-001/shd")
        assert r.status_code == 404

    def test_options_returns_200(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/properties/PROP-001/shd")
        assert r.status_code == 200

    def test_valid_property_returns_200(self, shd_env):
        r = shd_env.get("/api/v1/properties/PROP-001/shd")
        assert r.status_code == 200

    def test_valid_property_status_success(self, shd_env):
        r = shd_env.get("/api/v1/properties/PROP-001/shd")
        assert r.get_json()["status"] == "success"

    def test_valid_property_has_data(self, shd_env):
        r = shd_env.get("/api/v1/properties/PROP-001/shd")
        assert "data" in r.get_json()

    def test_unknown_property_returns_404(self, shd_env):
        r = shd_env.get("/api/v1/properties/PROP-MISSING/shd")
        assert r.status_code == 404

    def test_unknown_property_status_error(self, shd_env):
        r = shd_env.get("/api/v1/properties/PROP-MISSING/shd")
        assert r.get_json()["status"] == "error"


# ---------------------------------------------------------------------------
# GET /api/v1/properties/<prop_id>/she
# ---------------------------------------------------------------------------

class TestPropertyShe:

    def test_no_data_returns_404(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/properties/PROP-001/she")
        assert r.status_code == 404

    def test_options_returns_200(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/properties/PROP-001/she")
        assert r.status_code == 200

    def test_valid_property_returns_200(self, she_env):
        r = she_env.get("/api/v1/properties/PROP-001/she")
        assert r.status_code == 200

    def test_valid_property_status_success(self, she_env):
        r = she_env.get("/api/v1/properties/PROP-001/she")
        assert r.get_json()["status"] == "success"

    def test_valid_property_has_data(self, she_env):
        r = she_env.get("/api/v1/properties/PROP-001/she")
        assert "data" in r.get_json()

    def test_unknown_property_returns_404(self, she_env):
        r = she_env.get("/api/v1/properties/PROP-MISSING/she")
        assert r.status_code == 404

    def test_unknown_property_status_error(self, she_env):
        r = she_env.get("/api/v1/properties/PROP-MISSING/she")
        assert r.get_json()["status"] == "error"
