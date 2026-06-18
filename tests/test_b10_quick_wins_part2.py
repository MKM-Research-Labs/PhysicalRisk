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
Block B10 quick-win coverage tests. (part 2)

Each test targets 1-2 uncovered statements in files that are already
at 93-98 % coverage, pushing them to 99-100 %.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# 9. storm_factory.py line 107 — else branch (unknown IntensityProfile)
# ---------------------------------------------------------------------------

class TestStormFactoryElseBranch:

    def test_create_storm_linear_fallback(self):
        """Unknown intensity profile falls to else: intensity = peak * t_frac."""
        from models.stormgauge.storm_factory import create_storm

        # Use a mock that doesn't match TRIANGULAR/GAUSSIAN/BETA
        unknown_profile = MagicMock()
        unknown_profile.__eq__ = lambda self, other: False

        storm = create_storm(
            track_start=(0.0, 0.0),
            track_end=(2.0, 0.0),
            peak_intensity=50.0,
            intensity_profile=unknown_profile,
            num_track_points=5,
        )
        assert storm.storm_id.startswith("STORM-")
        assert len(storm.track) == 5
        # First point at t_frac=0 should have intensity = 50*0 = 0
        assert storm.track[0].intensity == 0.0


# ---------------------------------------------------------------------------
# 10. gaugehd/directory.py line 81 — if __name__ == "__main__": main()
# ---------------------------------------------------------------------------

class TestGaugehdDirectoryMain:

    def test_main_function_exists(self):
        """directory.main() is callable."""
        from port.cdm.gaugehd.directory import main
        assert callable(main)


# ---------------------------------------------------------------------------
# 11. insurance.py line 67 — area exceeds all finite thresholds
# ---------------------------------------------------------------------------

class TestInsuranceAreaFallback:

    def test_area_infinity_falls_through(self):
        """Area = float('inf') skips all threshold checks, hits fallback."""
        from models.valuation.insurance import get_area_premium_factor_range

        result = get_area_premium_factor_range(float('inf'))
        assert isinstance(result, tuple)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# 12. tradingdesk.py line 363 — get_statistics() method
# ---------------------------------------------------------------------------

class TestTradingDeskStatistics:

    def test_get_statistics_returns_dimensions(self):
        """get_statistics() returns panel_width and panel_height."""
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel

        td = TradingDeskPanel.__new__(TradingDeskPanel)
        td.panel_width = "420px"
        td.panel_height = "600px"

        stats = td.get_statistics()
        assert stats["panel_width"] == "420px"
        assert stats["panel_height"] == "600px"


# ---------------------------------------------------------------------------
# 13. property/main/encoder.py line 37 — super().default(obj) fallback
# ---------------------------------------------------------------------------

class TestPropertyMainEncoderFallback:

    def test_unhandled_type_raises_typeerror(self):
        """Passing an unhandled type triggers super().default() → TypeError."""
        from port.src.property.main.encoder import DateTimeEncoder

        encoder = DateTimeEncoder()
        with pytest.raises(TypeError):
            encoder.default(set([1, 2, 3]))


# ---------------------------------------------------------------------------
# 14. property/ts/encoder.py line 22 — np.floating handling
# ---------------------------------------------------------------------------

class TestPropertyTsEncoderFloating:

    def test_numpy_floating_encoded_as_float(self):
        """np.float64 is converted to Python float by encoder."""
        from port.src.property.ts.encoder import DateTimeEncoder

        encoder = DateTimeEncoder()
        result = encoder.default(np.float64(3.14))
        assert isinstance(result, float)
        assert abs(result - 3.14) < 1e-10


# ---------------------------------------------------------------------------
# 15. visual/factory.py line 28 — create_visualization()
# ---------------------------------------------------------------------------

class TestVisualFactory:

    def test_create_visualization_returns_instance(self, tmp_path):
        """create_visualization() returns a TCEventVisualization instance."""
        from visual.factory import create_visualization
        from visual.core.visualizer import TCEventVisualization

        viz = create_visualization(
            input_dir=str(tmp_path),
            output_dir=str(tmp_path),
        )
        assert isinstance(viz, TCEventVisualization)
