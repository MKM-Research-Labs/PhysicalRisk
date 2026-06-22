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

"""Autouse fixture binding the data backend for every test.

As callers migrate onto the ``database`` package (coding rule R6), they need a
backend configured. This binds the config-wired file backend before each test
(resolving the same real paths ``create_app`` uses, so read-path tests work) —
but **with writes to the real ``data/`` tree refused** (``_WriteGuardedFileRepository``).
A test that needs to write must bind a scratch backend (``tmp_catchment`` /
``memory_catchment``) or monkeypatch ``config`` paths to a tmp dir first; otherwise
the guard raises rather than letting a migrated writer silently clobber real
portfolio data on the shared SSD. Tests that need a different backend (e.g. the
database suite) override this and may reset to ``None``; the fixture re-binds for
the next test.
"""

import pytest


@pytest.fixture(autouse=True)
def _database_file_backend():
    from db_helpers import use_guarded_file_backend
    use_guarded_file_backend()
    yield
