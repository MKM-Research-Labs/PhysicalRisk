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

"""Tests for stress infrastructure — part 2: legacy fallback paths."""

from unittest.mock import patch

import pytest


class TestLoadStressStormLegacySearch:
    """_load_stress_storm searches legacy monolithic file."""

    def test_single_storm_from_legacy_file(self, stress_env):
        """Storm loaded by searching legacy storms list."""
        import routes.trading.stress._helpers as stress_helpers

        ss_dir = stress_env['input_dir'] / 'stress_storms'
        storm_file = ss_dir / 'LEGACY-STORM-001.json'
        if storm_file.exists():
            storm_file.unlink()

        legacy_data = {
            "storms": [
                {"storm_id": "LEGACY-STORM-001", "severity": "severe"},
                {"storm_id": "LEGACY-STORM-002", "severity": "minor"},
            ]
        }
        with patch.object(stress_helpers, '_load_stress_storms', return_value=legacy_data):
            result = stress_helpers._load_stress_storm("LEGACY-STORM-001")
        assert result is not None
        assert result["storm_id"] == "LEGACY-STORM-001"

        with patch.object(stress_helpers, '_load_stress_storms', return_value=legacy_data):
            result2 = stress_helpers._load_stress_storm("NONEXISTENT")
        assert result2 is None
