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

"""WP2.4 step 1 — run-scoped catchment context (``database.context``)."""

import contextvars

import pytest

import database
from database import active_catchment, catchment_context
from config import config


def test_falls_back_to_config_when_unbound():
    """With no context bound, the active catchment is config's process-wide one."""
    assert active_catchment() == config.catchment_id


def test_context_overrides_active_catchment():
    with catchment_context("halong") as bound:
        assert bound == "halong"
        assert active_catchment() == "halong"


def test_context_restores_on_exit():
    before = active_catchment()
    with catchment_context("halong"):
        pass
    assert active_catchment() == before


def test_nested_contexts_restore_inner_then_outer():
    with catchment_context("halong"):
        assert active_catchment() == "halong"
        with catchment_context("mekong"):
            assert active_catchment() == "mekong"
        # inner unwinds back to the outer value, not the global default
        assert active_catchment() == "halong"
    assert active_catchment() == config.catchment_id


def test_reset_happens_even_on_exception():
    before = active_catchment()
    with pytest.raises(RuntimeError, match="boom"):
        with catchment_context("halong"):
            assert active_catchment() == "halong"
            raise RuntimeError("boom")
    assert active_catchment() == before


def test_contextvar_isolated_across_logical_contexts():
    """A binding in one contextvars context does not leak into another."""
    seen = {}

    def read_in_fresh_context():
        # a copied context starts from the current state; bind here and confirm
        # the binding stays local to this context object.
        with catchment_context("mekong"):
            seen["inner"] = active_catchment()

    with catchment_context("halong"):
        ctx = contextvars.copy_context()
        ctx.run(read_in_fresh_context)
        # the copied context's "mekong" binding did not bleed back into ours
        assert seen["inner"] == "mekong"
        assert active_catchment() == "halong"


def test_reexported_from_package_root():
    assert database.active_catchment is active_catchment
    assert database.catchment_context is catchment_context
