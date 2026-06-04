# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Tests for the wind-coupled peril scenario routes (win / faw / fow).

Covers:
  GET /api/v1/properties/<prop_id>/win   (wind-only)
  GET /api/v1/properties/<prop_id>/faw   (flood AND wind)
  GET /api/v1/properties/<prop_id>/fow   (flood OR wind)

These mirror the shd/she/bri routes: 404 when the scenario file is absent,
200 OK preflight, success payload for a known asset, 404 for an unknown one.
"""


class TestPropertyWin:

    def test_no_data_returns_404(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/properties/PROP-001/win")
        assert r.status_code == 404

    def test_options_returns_200(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/properties/PROP-001/win")
        assert r.status_code == 200

    def test_valid_property_returns_200(self, win_env):
        r = win_env.get("/api/v1/properties/PROP-001/win")
        assert r.status_code == 200

    def test_valid_property_status_success(self, win_env):
        r = win_env.get("/api/v1/properties/PROP-001/win")
        assert r.get_json()["status"] == "success"

    def test_valid_property_has_data(self, win_env):
        r = win_env.get("/api/v1/properties/PROP-001/win")
        assert "data" in r.get_json()

    def test_unknown_property_returns_404(self, win_env):
        r = win_env.get("/api/v1/properties/PROP-MISSING/win")
        assert r.status_code == 404


class TestPropertyFaw:

    def test_no_data_returns_404(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/properties/PROP-001/faw")
        assert r.status_code == 404

    def test_options_returns_200(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/properties/PROP-001/faw")
        assert r.status_code == 200

    def test_valid_property_returns_200(self, faw_env):
        r = faw_env.get("/api/v1/properties/PROP-001/faw")
        assert r.status_code == 200

    def test_valid_property_status_success(self, faw_env):
        r = faw_env.get("/api/v1/properties/PROP-001/faw")
        assert r.get_json()["status"] == "success"

    def test_unknown_property_returns_404(self, faw_env):
        r = faw_env.get("/api/v1/properties/PROP-MISSING/faw")
        assert r.status_code == 404


class TestPropertyFow:

    def test_no_data_returns_404(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/properties/PROP-001/fow")
        assert r.status_code == 404

    def test_options_returns_200(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/properties/PROP-001/fow")
        assert r.status_code == 200

    def test_valid_property_returns_200(self, fow_env):
        r = fow_env.get("/api/v1/properties/PROP-001/fow")
        assert r.status_code == 200

    def test_valid_property_status_success(self, fow_env):
        r = fow_env.get("/api/v1/properties/PROP-001/fow")
        assert r.get_json()["status"] == "success"

    def test_unknown_property_returns_404(self, fow_env):
        r = fow_env.get("/api/v1/properties/PROP-MISSING/fow")
        assert r.status_code == 404
