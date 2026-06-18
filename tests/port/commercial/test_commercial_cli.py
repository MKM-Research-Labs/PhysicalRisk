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

"""CLI argument wiring tests for `python app.py port --commercial`.

These exercise the parser and the segment-flag membership — they do NOT
run the full pipeline (that is covered by the generator integration
tests). The point is to catch regressions like the one where
``args.commercial`` was missing from ``segment_flags`` and a bare
``--commercial`` invocation accidentally triggered ``run_all``.
"""

import argparse

import pytest

from app.commands.port import register_parser


@pytest.fixture
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    register_parser(sub)
    return p


class TestCommercialFlag:

    def test_commercial_flag_present(self, parser):
        ns = parser.parse_args(["port", "--commercial"])
        assert ns.commercial is True

    def test_commercial_short_alias(self, parser):
        ns = parser.parse_args(["port", "--co"])
        assert ns.commercial is True

    def test_commercial_default_false(self, parser):
        ns = parser.parse_args(["port"])
        assert ns.commercial is False

    def test_num_commercial_default(self, parser):
        ns = parser.parse_args(["port", "--commercial"])
        assert ns.num_commercial == 10

    def test_num_commercial_override(self, parser):
        ns = parser.parse_args(["port", "--commercial", "--num-commercial", "25"])
        assert ns.num_commercial == 25

    def test_num_commercial_short_alias(self, parser):
        ns = parser.parse_args(["port", "--commercial", "-nc", "7"])
        assert ns.num_commercial == 7


class TestSegmentFlagMembership:
    """Regression: bare --commercial must NOT enable run_all.

    The bug we fixed was that ``segment_flags`` did not include
    ``args.commercial``, so a bare ``--commercial`` set all other flags
    false and the ``run_all = not any(segment_flags)`` shortcut tripped,
    running the full residential pipeline by accident.
    """

    def test_commercial_in_segment_flags_definition(self):
        # Read the orchestrator source and confirm args.commercial is in
        # segment_flags so any future refactor keeps the invariant.
        from pathlib import Path
        src = Path("app/commands/port/orchestrator.py").read_text()
        import re
        m = re.search(r"segment_flags\s*=\s*\[(.*?)\]", src, re.DOTALL)
        assert m, "segment_flags assignment not found in orchestrator.py"
        assert "args.commercial" in m.group(1), (
            "args.commercial must be part of segment_flags so a bare "
            "--commercial does not trip the run_all shortcut")
