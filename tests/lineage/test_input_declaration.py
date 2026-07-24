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

"""A stage must record every input its lineage topology declares.

Recording fewer inputs than the topology declares has two consequences, and
the second is the serious one:

1. The step reports **stale after every successful run**, because the freshness
   check cannot verify an input for which no hash was ever recorded. A warning
   that always fires trains readers to ignore it — which is exactly what
   happened here: the peril timeseries steps reported stale for days, the
   warning was assumed to mean the steps had not run, and that assumption sent
   a root-cause investigation in the wrong direction.

2. **The lineage graph has a hole.** A change to the undeclared artefact never
   invalidates the consuming step, so a downstream output can silently be built
   from a stale input. That is the BCBS 239 claim this machinery exists to
   support.

The guard is in ``StageContext.record``; these tests pin its behaviour.
"""

import pytest

from app.commands.port.context import StageContext


class TestUndeclaredInputWarning:

    def test_a_complete_record_is_silent(self, capsys):
        from lineage.validation import STEP_IO

        declared = STEP_IO["property_peril_ts"]["inputs"]
        StageContext._warn_undeclared_inputs(
            "property_peril_ts", {name: object() for name in declared})
        assert capsys.readouterr().out == ""

    def test_a_missing_input_is_named(self, capsys):
        """The regression: bow/baw read the BRI-resilient spine, so omitting it
        both cried wolf and left the change-detection gap."""
        from lineage.validation import STEP_IO

        declared = set(STEP_IO["property_peril_ts"]["inputs"])
        assert "propertytsb/" in declared, "topology no longer declares the BRI spine"

        without = {n: object() for n in declared - {"propertytsb/"}}
        StageContext._warn_undeclared_inputs("property_peril_ts", without)

        out = capsys.readouterr().out
        assert "propertytsb/" in out
        assert "property_peril_ts" in out

    def test_an_unknown_step_is_ignored(self, capsys):
        """Steps outside the topology are not the topology's business."""
        StageContext._warn_undeclared_inputs("not-a-step", {"anything": object()})
        assert capsys.readouterr().out == ""

    def test_no_inputs_recorded_at_all_is_reported(self, capsys):
        StageContext._warn_undeclared_inputs("property_peril_ts", None)
        assert "property_peril_ts" in capsys.readouterr().out

    def test_the_guard_never_raises(self):
        """A lineage-completeness problem must not abort an otherwise sound
        generation run."""
        for inputs in (None, {}, {"unexpected/": object()}):
            StageContext._warn_undeclared_inputs("property_peril_ts", inputs)


# A manifest-level assertion was considered here and deliberately left out.
# It would assert a property of the data on disk, not of the code, and would
# fail until someone re-ran the port — the same cry-wolf pattern this fix
# exists to remove. The recorded manifest self-corrects on the next run; the
# guard in StageContext.record and the source checks below are what keep the
# code honest in the meantime.

class TestPerilStagesDeclareTheBriSpine:
    """The two stages the gap was found in, pinned directly.

    Asserted against the stage source rather than by running it: the stages
    need a populated data directory, and the property under test is a
    declaration, not a behaviour.
    """

    @pytest.mark.parametrize(
        "module_path,expected",
        [
            ("app/commands/port/stages/windhazard/property.py", "propertytsb/"),
            ("app/commands/port/stages/windhazard/commercial.py", "commercialtsb/"),
        ],
    )
    def test_the_stage_records_the_bri_spine(self, module_path, expected):
        from pathlib import Path

        source = Path(module_path).read_text()
        assert f'"{expected}"' in source, (
            f"{module_path} does not record {expected}; bow/baw read it, so "
            "omitting it reopens the lineage gap"
        )
