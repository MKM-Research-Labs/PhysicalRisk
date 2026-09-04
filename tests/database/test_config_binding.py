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
    # any other catchment composes <input root>/<catchment>
    other = "halong" if active != "halong" else "mekong"
    # get_input_root(), not project_root/"data"/"input": the composed literal
    # ignored MKM_DATA_ROOT, so this asserted the real tree while the repo
    # under test resolved to whichever root was actually configured.
    assert repo._catchment_dir(other) == config.get_input_root() / other


def test_use_file_backend_installs_active_repo():
    try:
        repo = config_binding.use_file_backend()
        assert isinstance(repo, FileRepository)
        # the package now resolves through the configured backend
        assert isinstance(database.catchments(), list)
        assert database.ping() is True
    finally:
        database.configure_backend(None)
