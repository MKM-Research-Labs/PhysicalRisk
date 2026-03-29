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
Import-isolation tests for port.src — part 2.

Covers: TestGeopandasIsolation, TestCmdPortLazyBookImport.
"""

import importlib
import sys

import pytest

from tests.port.conftest_import_isolation import (
    _simulate_no_quantlib,
)


# ---------------------------------------------------------------------------
# Tests: geopandas isolation
# ---------------------------------------------------------------------------

class TestGeopandasIsolation:
    """
    geopandas is an optional GIS dependency used only in FloodRiskModel,
    build_correlation_matrix, and the full depth-damage/calculate_flood_depths
    functions.  scalar_depth_damage (used by propertyts) must not require it.
    """

    def _simulate_no_geopandas(self, monkeypatch):
        for key in list(sys.modules.keys()):
            if key == 'geopandas' or key.startswith('geopandas.'):
                monkeypatch.delitem(sys.modules, key, raising=False)
        monkeypatch.setitem(sys.modules, 'geopandas', None)

    def _drop_floodrisk_cache(self, monkeypatch):
        for key in list(sys.modules.keys()):
            if key.startswith('models.floodrisk'):
                monkeypatch.delitem(sys.modules, key, raising=False)

    def test_spatial_importable_without_geopandas(self, monkeypatch):
        self._simulate_no_geopandas(monkeypatch)
        self._drop_floodrisk_cache(monkeypatch)
        mod = importlib.import_module('models.floodrisk.spatial')
        assert hasattr(mod, 'haversine_distance')

    def test_depth_damage_importable_without_geopandas(self, monkeypatch):
        self._simulate_no_geopandas(monkeypatch)
        self._drop_floodrisk_cache(monkeypatch)
        mod = importlib.import_module('models.floodrisk.depth_damage')
        assert hasattr(mod, 'scalar_depth_damage')

    def test_scalar_depth_damage_works_without_geopandas(self, monkeypatch):
        self._simulate_no_geopandas(monkeypatch)
        self._drop_floodrisk_cache(monkeypatch)
        mod = importlib.import_module('models.floodrisk.depth_damage')
        result = mod.scalar_depth_damage(0.5)
        assert 0.0 < result <= 1.0

    def test_floodrisk_init_does_not_import_flood_risk_model(self):
        """__init__.py must not have an executable FloodRiskModel import statement."""
        import inspect
        import models.floodrisk as pkg
        src = inspect.getsource(pkg)
        # Filter out comment lines -- only check non-comment lines
        executable = '\n'.join(
            line for line in src.splitlines()
            if not line.strip().startswith('#')
        )
        assert 'FloodRiskModel' not in executable, (
            'models/floodrisk/__init__.py has an executable import of FloodRiskModel; '
            'this requires geopandas at import time for all floodrisk users.'
        )

    def test_propertyts_importable_without_geopandas(self, monkeypatch):
        """propertyts imports scalar_depth_damage -- must work without geopandas."""
        self._simulate_no_geopandas(monkeypatch)
        self._drop_floodrisk_cache(monkeypatch)
        for key in list(sys.modules.keys()):
            if key.startswith('port.src.property.propertyts'):
                monkeypatch.delitem(sys.modules, key, raising=False)
        mod = importlib.import_module('port.src.property.propertyts')
        assert hasattr(mod, 'PropertyTimeSeriesGenerator')


# ---------------------------------------------------------------------------
# Tests: cmd_port imports book lazily
# ---------------------------------------------------------------------------

class TestCmdPortLazyBookImport:

    def test_cmd_port_module_importable_without_quantlib(self, monkeypatch):
        """
        Importing app.commands.port must not trigger QuantLib.
        Only calling cmd_port() with --blotter should require it.
        """
        _simulate_no_quantlib(monkeypatch)
        for key in list(sys.modules.keys()):
            if key == "app.commands.port":
                monkeypatch.delitem(sys.modules, key, raising=False)
        mod = importlib.import_module("app.commands.port")
        assert hasattr(mod, "cmd_port")
        assert hasattr(mod, "register_parser")

    def test_book_import_inside_blotter_block(self):
        """
        The `from port.src.book import ...` statement in cmd_port must be
        inside the `if run_all or args.blotter:` block, not at module level.
        """
        import inspect
        from app.commands import port as _port_cmd
        src = inspect.getsource(_port_cmd)

        # The book import must appear after the blotter condition line
        blotter_idx = src.find("if run_all or args.blotter:")
        book_idx = src.find("from port.src.book import")

        assert blotter_idx != -1, "Could not find blotter block in cmd_port source"
        assert book_idx != -1, "Could not find book import in cmd_port source"
        assert book_idx > blotter_idx, (
            "from port.src.book import appears BEFORE the blotter block -- "
            "this means QuantLib is required even for non-book steps."
        )
