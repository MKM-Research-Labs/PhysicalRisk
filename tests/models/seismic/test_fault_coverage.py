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

"""Coverage tests for models.seismic.occurrence._fault — parse guard, file
load/path helpers, the beyond-end locate branch and single-point JB distance."""

import json

import pytest

from models.seismic.occurrence import _fault


class TestFaultCoverage:
    def test_parse_rejects_short_vertex(self):
        with pytest.raises(ValueError):
            _fault.parse_fault_trace([[1.0]])  # vertex len < 2 -> line 39

    def test_load_fault_trace_from_file(self, tmp_path):
        p = tmp_path / "fault_trace.json"
        p.write_text(json.dumps([[107.0, 20.9], [107.1, 21.0]]))
        fault = _fault.load_fault_trace(p)  # line 49
        assert fault == [(20.9, 107.0), (21.0, 107.1)]

    def test_fault_trace_path(self, tmp_path):
        assert _fault.fault_trace_path(tmp_path) == tmp_path / "fault_trace.json"  # 54

    def test_locate_beyond_total_returns_last_segment(self):
        cum = [0.0, 1.0, 2.0]
        assert _fault.locate(cum, 99.0) == (len(cum) - 2, 1.0)  # line 76

    def test_joyner_boore_single_point_segment(self):
        # A one-vertex segment uses the direct haversine branch (line 104).
        d = _fault.joyner_boore_distance_km(20.9, 107.0, [(21.0, 107.1)])
        assert d >= 0.0
