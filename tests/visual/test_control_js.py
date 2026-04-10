# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Contract tests for Control tab JavaScript output.

Validates that the Control tab DOM builder and data functions export the
expected function names, DOM element IDs, and event handlers.
"""

import pytest

from tests.visual.conftest import iife_src_file, iife_has_node, iife_node_check


# ---------------------------------------------------------------------------
# Control tab JS — function exports
# ---------------------------------------------------------------------------

class TestControlTabFunctionExports:
    """Control tab JS must export required functions."""

    @pytest.fixture(scope='class')
    def dom_js(self):
        return iife_src_file(
            'src/visual/interactivity/storm/sp_control/setup_dom.py'
        )

    @pytest.fixture(scope='class')
    def data_js(self):
        return iife_src_file(
            'src/visual/interactivity/storm/sp_control/setup_data.py'
        )

    def test_create_control_view_exists(self, dom_js):
        """setup_dom.py must define createControlView()."""
        assert 'function createControlView' in dom_js

    def test_ctrl_mark_dirty_exists(self, dom_js):
        """setup_dom.py must define ctrlMarkDirty()."""
        assert 'function ctrlMarkDirty' in dom_js

    def test_ctrl_clear_dirty_exists(self, dom_js):
        """setup_dom.py must define ctrlClearDirty()."""
        assert 'function ctrlClearDirty' in dom_js

    def test_load_control_data_exists(self, data_js):
        """setup_data.py must define loadControlData()."""
        assert 'function loadControlData' in data_js

    def test_save_control_data_exists(self, data_js):
        """setup_data.py must define saveControlData()."""
        assert 'function saveControlData' in data_js

    def test_reset_control_data_exists(self, data_js):
        """setup_data.py must define resetControlData()."""
        assert 'function resetControlData' in data_js

    def test_ctrl_collect_exists(self, data_js):
        """setup_data.py must define _ctrlCollect() for form value gathering."""
        assert 'function _ctrlCollect' in data_js

    def test_ctrl_render_section_exists(self, data_js):
        """setup_data.py must define _ctrlRenderSection()."""
        assert 'function _ctrlRenderSection' in data_js


# ---------------------------------------------------------------------------
# Control tab JS — DOM element IDs
# ---------------------------------------------------------------------------

class TestControlTabDomElements:
    """Control tab must create elements with expected IDs."""

    @pytest.fixture(scope='class')
    def dom_js(self):
        return iife_src_file(
            'src/visual/interactivity/storm/sp_control/setup_dom.py'
        )

    def test_has_view_id(self, dom_js):
        """View container must have id='sp-control-view'."""
        assert 'sp-control-view' in dom_js

    def test_has_save_button_id(self, dom_js):
        """Save button must have id='sp-ctrl-save-btn'."""
        assert 'sp-ctrl-save-btn' in dom_js

    def test_has_reset_button_id(self, dom_js):
        """Reset button must have id='sp-ctrl-reset-btn'."""
        assert 'sp-ctrl-reset-btn' in dom_js

    def test_has_dirty_indicator_id(self, dom_js):
        """Dirty indicator must have id='sp-ctrl-dirty'."""
        assert 'sp-ctrl-dirty' in dom_js

    def test_has_body_id(self, dom_js):
        """Scrollable body must have id='sp-ctrl-body'."""
        assert 'sp-ctrl-body' in dom_js

    def test_has_status_bar_id(self, dom_js):
        """Status bar must have id='sp-ctrl-status'."""
        assert 'sp-ctrl-status' in dom_js

    def test_has_all_section_ids(self, dom_js):
        """Section IDs are built dynamically from the sections array.
        Verify the array contains all five section id strings."""
        for section_id in ('storm_generation', 'hydrograph_synthesis',
                           'gauge_propagation', 'spatial_correlation',
                           'stress_catalogue'):
            assert section_id in dom_js, (
                f"Missing section id string: {section_id}"
            )

    def test_section_id_prefix_pattern(self, dom_js):
        """Section elements use 'sp-ctrl-section-' prefix concatenation."""
        assert 'sp-ctrl-section-' in dom_js

    def test_arrow_id_prefix_pattern(self, dom_js):
        """Arrow elements use 'sp-ctrl-arrow-' prefix concatenation."""
        assert 'sp-ctrl-arrow-' in dom_js


# ---------------------------------------------------------------------------
# Control tab JS — data field definitions
# ---------------------------------------------------------------------------

class TestControlTabFieldDefinitions:
    """Data loader must define fields for all five sections."""

    @pytest.fixture(scope='class')
    def data_js(self):
        return iife_src_file(
            'src/visual/interactivity/storm/sp_control/setup_data.py'
        )

    def test_has_field_defs_for_all_sections(self, data_js):
        """_ctrlFields must define fields for all five sections."""
        for section in ('storm_generation', 'hydrograph_synthesis',
                        'gauge_propagation', 'spatial_correlation',
                        'stress_catalogue'):
            assert section in data_js, f"Missing field defs for {section}"

    def test_storm_generation_has_event_window(self, data_js):
        """Storm generation fields must include event_window_hours."""
        assert 'event_window_hours' in data_js

    def test_hydrograph_has_saturation_beta(self, data_js):
        """Hydrograph fields must include saturation_beta."""
        assert 'saturation_beta' in data_js

    def test_gauge_prop_has_default_roughness(self, data_js):
        """Gauge propagation fields must include default_roughness."""
        assert 'default_roughness' in data_js

    def test_spatial_has_range_km(self, data_js):
        """Spatial correlation fields must include range_km."""
        assert 'spatial_corr_base_range_km' in data_js

    def test_stress_has_min_count(self, data_js):
        """Stress catalogue fields must include min storm count."""
        assert 'stress_storms_min_count' in data_js

    def test_api_endpoint_correct(self, data_js):
        """API endpoint in fetch calls must be correct."""
        assert '/api/v1/trading/control/params' in data_js
        assert '/api/v1/trading/control/reset' in data_js


# ---------------------------------------------------------------------------
# Control tab JS — field renderer functions
# ---------------------------------------------------------------------------

class TestControlTabFieldRenderers:
    """DOM module must define scalar, dict, and array field renderers."""

    @pytest.fixture(scope='class')
    def dom_js(self):
        return iife_src_file(
            'src/visual/interactivity/storm/sp_control/setup_dom.py'
        )

    def test_scalar_field_renderer(self, dom_js):
        """_ctrlScalarField must be defined for number/checkbox inputs."""
        assert 'function _ctrlScalarField' in dom_js

    def test_dict_field_renderer(self, dom_js):
        """_ctrlDictField must be defined for dict parameter tables."""
        assert 'function _ctrlDictField' in dom_js

    def test_array_field_renderer(self, dom_js):
        """_ctrlArrayField must be defined for array parameter rows."""
        assert 'function _ctrlArrayField' in dom_js

    def test_data_ctrl_key_attribute(self, dom_js):
        """Field renderers must use data-ctrl-key attributes."""
        assert 'data-ctrl-key' in dom_js

    def test_oninput_dirty_handler(self, dom_js):
        """Inputs must call ctrlMarkDirty() on change."""
        assert 'ctrlMarkDirty()' in dom_js


# ---------------------------------------------------------------------------
# Panel integration — tab registration
# ---------------------------------------------------------------------------

class TestControlTabRegistration:
    """Control tab must be registered in Storm Portfolio chrome.py."""

    def test_chrome_has_control_tab_button(self):
        src = iife_src_file(
            'src/visual/interactivity/storm/stormportfolio/chrome.py'
        )
        assert 'sp-tab-control' in src

    def test_chrome_has_control_view_creation(self):
        src = iife_src_file(
            'src/visual/interactivity/storm/stormportfolio/chrome.py'
        )
        assert 'createControlView' in src

    def test_chrome_has_control_tab_switching(self):
        src = iife_src_file(
            'src/visual/interactivity/storm/stormportfolio/chrome.py'
        )
        assert 'loadControlData' in src
