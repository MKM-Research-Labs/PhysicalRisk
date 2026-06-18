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

import json
from unittest.mock import patch

import pytest


class TestLegacyFallbackPaths:
    """Legacy stress_storms.json fallback loading."""

    def test_legacy_file_loaded_when_no_index(self, stress_env):
        """Falls back to stress_storms.json when _index.json absent."""
        import routes.trading.stress._helpers as stress_helpers
        stress_helpers._stress_index_cache = None
        stress_helpers._stress_index_mtime = None

        index_path = stress_env['input_dir'] / 'stress_storms' / '_index.json'
        if index_path.exists():
            index_path.unlink()
        ss_dir = stress_env['input_dir'] / 'stress_storms'
        if ss_dir.exists():
            import shutil
            shutil.rmtree(ss_dir)

        legacy_path = stress_env['input_dir'] / 'stress_storms.json'
        legacy_data = {"storms": [{"storm_id": "LEGACY-001", "severity": "severe"}]}
        legacy_path.write_text(json.dumps(legacy_data))

        result = stress_helpers._load_stress_storms()
        assert result is not None
        assert result["storms"][0]["storm_id"] == "LEGACY-001"

        stress_helpers._stress_index_cache = None
        stress_helpers._stress_index_mtime = None

    def test_legacy_cache_reuse(self, stress_env):
        """Legacy file uses mtime cache — second call returns cached."""
        import routes.trading.stress._helpers as stress_helpers
        stress_helpers._stress_index_cache = None
        stress_helpers._stress_index_mtime = None

        ss_dir = stress_env['input_dir'] / 'stress_storms'
        if ss_dir.exists():
            import shutil
            shutil.rmtree(ss_dir)

        legacy_path = stress_env['input_dir'] / 'stress_storms.json'
        legacy_data = {"storms": [{"storm_id": "LEGACY-002"}]}
        legacy_path.write_text(json.dumps(legacy_data))

        r1 = stress_helpers._load_stress_storms()
        assert r1["storms"][0]["storm_id"] == "LEGACY-002"

        r2 = stress_helpers._load_stress_storms()
        assert r2 is r1  # same object — cache hit

        stress_helpers._stress_index_cache = None
        stress_helpers._stress_index_mtime = None

    def test_legacy_stat_oserror_returns_cache(self, stress_env):
        """OSError on legacy file stat returns existing cache."""
        import routes.trading.stress._helpers as stress_helpers
        stress_helpers._stress_index_cache = {"storms": [{"storm_id": "cached-legacy"}]}
        stress_helpers._stress_index_mtime = 99999.0

        ss_dir = stress_env['input_dir'] / 'stress_storms'
        if ss_dir.exists():
            import shutil
            shutil.rmtree(ss_dir)

        legacy_path = stress_env['input_dir'] / 'stress_storms.json'
        legacy_path.write_text('{"storms": []}')

        real_stat = type(legacy_path).stat
        legacy_stat_calls = [0]
        def stat_side_effect(self_path, *a, **kw):
            if str(self_path).endswith('stress_storms.json'):
                legacy_stat_calls[0] += 1
                if legacy_stat_calls[0] >= 2:
                    raise OSError('disk')
            return real_stat(self_path, *a, **kw)

        with patch('pathlib.PosixPath.stat', stat_side_effect):
            result = stress_helpers._load_stress_storms()
        assert result == {"storms": [{"storm_id": "cached-legacy"}]}

        stress_helpers._stress_index_cache = None
        stress_helpers._stress_index_mtime = None


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
