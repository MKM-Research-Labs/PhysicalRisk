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

"""A missing/unreadable per-asset timeseries record must skip that asset,
not abort the whole hazard-curve build.

Regression: a stale or incomplete peril ts collection (e.g. a record the
iterator still lists but that can't be read, or a concurrent regeneration)
used to raise out of the per-asset read and crash the entire port at the
wind hazard-curve stage. The read now goes through the database seam in
``_generator``; the unreadable record is skipped there, and
``_process_property`` itself just returns ``None`` for a falsy record.
"""

import database
from port.src.property.hc.pricing._process import _ProcessMixin
from port.src.property.propertyhc import PropertyHazardCurveGenerator

from .conftest import write_property_ts


class _Host(_ProcessMixin):
    def __init__(self):
        self.logged = []

    def log(self, msg, *a, **k):
        self.logged.append(msg)


class TestProcessPropertyFalsyRecord:
    """_process_property is storage-agnostic: a falsy record returns None."""

    def test_none_record_returns_none(self):
        assert _Host()._process_property(None, {}, lambda *a, **k: None, 100) is None

    def test_empty_record_returns_none(self):
        assert _Host()._process_property({}, {}, lambda *a, **k: None, 100) is None


class TestGeneratorSkipsUnreadableRecord:
    """The generator skips an asset whose seam read raises, not crashing."""

    def test_unreadable_record_skipped(self, basic_output_dir, monkeypatch):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-good", n_floods=2)
        write_property_ts(pts_dir, "PROP-bad", n_floods=2)

        real = database.get_property_timeseries

        def flaky(catchment, asset_id, *a, **k):
            if asset_id == "PROP-bad":
                raise ValueError("corrupt record")
            return real(catchment, asset_id, *a, **k)

        monkeypatch.setattr(database, "get_property_timeseries", flaky)

        stats = PropertyHazardCurveGenerator(output_dir, verbose=False).generate()
        assert stats["properties_processed"] == 1
        assert stats["properties_skipped"] == 1
