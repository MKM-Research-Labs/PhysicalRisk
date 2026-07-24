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

"""Shared StageContext for the port pipeline stage modules.

Bundles everything a stage function needs (args, paths, lineage helpers,
generator modules) so each stage signature is a tight ``run(ctx)`` rather
than passing a dozen positional arguments.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional


@dataclass
class StageContext:
    """All shared state passed to stage functions."""

    args: Any                              # argparse.Namespace
    catchment: str
    output_dir: Path
    input_dir: Path
    run_id: Optional[str]
    run_all: bool

    # Lazy-imported pipeline modules.
    gauge: Any = None
    mortgage: Any = None
    hazard: Any = None
    counterparty: Any = None
    prop_gen: Any = None
    commercial_gen: Any = None
    commercial_loan_gen_cls: Any = None
    gaugehd: Any = None
    propertyts: Any = None
    propertyhc: Any = None

    # Lineage helpers — None when the lineage package isn't installed.
    record_step: Optional[Callable] = None
    pre_hash_inputs: Optional[Callable] = None
    get_stale_downstream: Optional[Callable] = None
    check_inputs_fresh: Optional[Callable] = None

    @property
    def commercial_exists(self) -> bool:
        """True when commercial.json is on disk (drives --all behaviour)."""
        return (self.input_dir / 'commercial.json').exists()

    def hash_inputs(self, inputs: dict) -> Any:
        """Hash inputs if lineage is available, else None."""
        return self.pre_hash_inputs(inputs) if self.pre_hash_inputs else None

    @staticmethod
    def _warn_undeclared_inputs(step_name: str, inputs: dict) -> None:
        """Warn when a stage records fewer inputs than the topology declares.

        A stage that reads an artefact but omits it here produces a permanent
        false "stale step" warning — the freshness check cannot verify an input
        with no recorded hash — and, worse, a silent lineage gap: a change to
        that artefact never invalidates this step. Both happened to the peril
        timeseries steps, which read the BRI-resilient spine for their bow/baw
        modes without declaring it, and reported stale after every successful
        run for as long as anyone had been looking.

        Reported rather than raised: a lineage-completeness problem should not
        abort a generation run that is otherwise sound.
        """
        try:
            from lineage.validation import STEP_IO
        except Exception:
            return  # lineage unavailable — nothing to check against
        declared = set((STEP_IO.get(step_name) or {}).get("inputs", ()))
        if not declared:
            return
        missing = declared - set(inputs or {})
        if missing:
            print(
                f"  [lineage] Warning: step '{step_name}' declares "
                f"{sorted(missing)} in the topology but did not record "
                "them; downstream freshness cannot be verified"
            )

    def record(self, **kwargs):
        """Wrap record_step + get_stale_downstream with a single helper.

        Pops ``stale_name`` (if present) to look up downstream dependencies
        after recording. Silently no-ops when lineage is unavailable.
        """
        if self.record_step is None:
            return
        stale_name = kwargs.pop("stale_name", None)
        if kwargs.get("step_name"):
            self._warn_undeclared_inputs(kwargs["step_name"], kwargs.get("inputs"))
        try:
            self.record_step(run_id=self.run_id, **kwargs)
            if stale_name and self.get_stale_downstream is not None:
                stale = self.get_stale_downstream(stale_name)
                if stale:
                    print(f"  ⚠ Dependencies require update: {', '.join(stale)}")
        except Exception as e:
            print(f"  [lineage] Warning: {e}")

    def strict_block(self, step_name: str) -> bool:
        """Return True (and print) if strict mode says inputs are stale."""
        if not self.args.strict or self.check_inputs_fresh is None:
            return False
        try:
            fresh, issues = self.check_inputs_fresh(step_name)
            if not fresh:
                print(f"\n  ✗ STRICT MODE: inputs stale for '{step_name}':")
                for issue in issues:
                    print(f"    - {issue}")
                print(f"  Run upstream steps first, or omit --strict.")
                return True
        except Exception:
            pass
        return False
