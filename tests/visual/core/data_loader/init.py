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

"""Tests for DataLoader.__init__."""

from pathlib import Path


class TestDataLoaderInit:

    def test_init_with_input_dir(self, tmp_path):
        from visual.core.data_loader import DataLoader
        dl = DataLoader(input_dir=tmp_path)
        assert dl.input_dir == tmp_path

    def test_init_with_string_path_converts_to_path(self, tmp_path):
        from visual.core.data_loader import DataLoader
        dl = DataLoader(input_dir=str(tmp_path))
        assert isinstance(dl.input_dir, Path)
        assert dl.input_dir == tmp_path

    def test_loaded_data_initialised(self, tmp_path):
        from visual.core.data_loader import DataLoader, LoadedData
        dl = DataLoader(input_dir=tmp_path)
        assert isinstance(dl.loaded_data, LoadedData)

    def test_validation_results_empty_at_init(self, tmp_path):
        from visual.core.data_loader import DataLoader
        dl = DataLoader(input_dir=tmp_path)
        assert dl._validation_results == {}

    def test_private_loaders_created(self, tmp_path):
        from visual.core.data_loader import DataLoader
        dl = DataLoader(input_dir=tmp_path)
        assert dl._gauge_loader is not None
        assert dl._property_loader is not None
        assert dl._rloan_loader is not None
