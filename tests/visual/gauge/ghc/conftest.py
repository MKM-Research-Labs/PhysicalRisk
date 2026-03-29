# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Shared fixtures for ghc historical detail tests."""

import pytest


@pytest.fixture(scope='module')
def hist_js():
    """Get Historical tab JS once for all tests."""
    from visual.interactivity.gauge.gaugehc import ghc_historical
    return ghc_historical.get_js()
