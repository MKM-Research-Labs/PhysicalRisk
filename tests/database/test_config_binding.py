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

"""Task 0.4 — the production config binding and the FileRepository dir-resolver."""

import pytest

import database
from database import config_binding
from database.file_repo import FileRepository
from config import config


def test_file_repo_requires_root_or_resolver():
    with pytest.raises(ValueError, match="input_root or dir_resolver"):
        FileRepository()


def test_custom_dir_resolver_routes_and_has_no_root_listing(tmp_path):
    repo = FileRepository(dir_resolver=lambda c: tmp_path / f"X-{c}")
    repo.save("gauge", "thames", [1])
    assert (tmp_path / "X-thames" / "gauge.json").exists()
    # no input_root supplied -> cannot enumerate catchments
    assert repo.catchments() == []


def test_from_config_active_catchment_honours_resolved_dir():
    repo = config_binding.from_config()
    active = config.catchment_id
    # active catchment routes through config.get_input_dir() (override-aware)
    assert repo._catchment_dir(active) == config.get_input_dir()
    # any other catchment composes data/input/<catchment>
    other = "halong" if active != "halong" else "mekong"
    assert repo._catchment_dir(other) == config.get_project_root() / "data" / "input" / other


def test_use_file_backend_installs_active_repo():
    try:
        repo = config_binding.use_file_backend()
        assert isinstance(repo, FileRepository)
        # the package now resolves through the configured backend
        assert isinstance(database.catchments(), list)
        assert database.ping() is True
    finally:
        database.configure_backend(None)
