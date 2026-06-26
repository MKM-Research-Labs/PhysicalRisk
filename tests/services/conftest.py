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

"""Pytest configuration for services tests."""

import pytest

import database
from db_helpers import tmp_catchment


@pytest.fixture(autouse=True)
def _services_catchment(temp_data_dir):
    """Bind an isolated catchment rooted at the test's ``temp_data_dir``.

    The entity loaders read their portfolio through the database seam (ignoring the
    ``data_dir`` they are constructed with), so binding the seam to ``temp_data_dir``
    makes them read exactly the JSON files these tests write there — restoring the
    pre-migration behaviour where a test's own files drove the loader. Tests that seed
    through ``populated_data_dir`` bind their own (nested) catchment on top of this."""
    with tmp_catchment(temp_data_dir):
        yield
