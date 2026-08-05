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

"""Tests for the mekong catchment shims.

``port.rand.mekong.{commercial.commercial_random, gauge.gauge_field_generators,
property.property_energy}`` are alias shims: each imports the shared canonical
module and replaces its own ``sys.modules`` entry with it, so every symbol
resolves through the single shared implementation. Importing each shim executes
that aliasing and the assertions confirm the mekong path *is* the shared module
object (not a forked copy).
"""

import sys


class TestCommercialRandomShim:

    def test_aliases_shared_canonical(self):
        from port.rand.mekong.commercial import commercial_random as mekong
        from port.rand.shared.commercial import commercial_random as shared
        assert mekong is shared

    def test_sys_modules_entry_is_canonical(self):
        import port.rand.mekong.commercial.commercial_random  # noqa: F401
        from port.rand.shared.commercial import commercial_random as shared
        assert sys.modules["port.rand.mekong.commercial.commercial_random"] is shared


class TestGaugeFieldGeneratorsShim:

    def test_aliases_shared_canonical(self):
        from port.rand.mekong.gauge import gauge_field_generators as mekong
        from port.rand.shared.gauge import gauge_field_generators as shared
        assert mekong is shared

    def test_sys_modules_entry_is_canonical(self):
        import port.rand.mekong.gauge.gauge_field_generators  # noqa: F401
        from port.rand.shared.gauge import gauge_field_generators as shared
        assert sys.modules["port.rand.mekong.gauge.gauge_field_generators"] is shared


class TestPropertyEnergyShim:

    def test_aliases_shared_canonical(self):
        from port.rand.mekong.property import property_energy as mekong
        from port.rand.shared.property import property_energy as shared
        assert mekong is shared

    def test_sys_modules_entry_is_canonical(self):
        import port.rand.mekong.property.property_energy  # noqa: F401
        from port.rand.shared.property import property_energy as shared
        assert sys.modules["port.rand.mekong.property.property_energy"] is shared
