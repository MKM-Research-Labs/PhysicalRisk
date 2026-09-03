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

"""RNG seeds for portfolio generation.

Generation randomness reaches the *global* RNGs — 313 call sites across 26
modules in ``src/port`` use ``random.foo()`` / ``np.random.foo()`` rather than
an injected generator — so reproducibility is achieved by seeding those globals
once, before any stage runs, not by threading a generator through every site.

The per-stage values below were previously hardcoded literals at their call
sites (``seed=42``, ``seed=43``). They live here so the same run can be
reproduced, and so a caller can shift the whole set with one ``--seed`` without
every stage collapsing onto an identical stream.
"""

# Offsets applied to a run seed, one per stage that takes its own seed. Distinct
# so two stages drawing the same number of values do not draw the *same* values.
SEED_OFFSETS = {
    "stressm": 0,
    "book": 1,
    "book_property": 2,
    "eod": 3,
    "typhoon": 4,
    "fire": 5,
    "seismic": 6,
}

# What each stage used before a run seed existed. Preserved exactly so a run
# with no --seed generates what it always did.
LEGACY_SEEDS = {
    "stressm": 42,
    "book": 42,
    "book_property": 42,
    "eod": 42,
}


def stage_seed(run_seed, stage):
    """Seed for *stage*: derived from *run_seed*, or the legacy default.

    ``run_seed is None`` reproduces pre-existing behaviour — the stages that had
    a hardcoded seed keep it, and the stages that had none stay
    nondeterministic (returning ``None`` lets them decide).
    """
    if run_seed is None:
        return LEGACY_SEEDS.get(stage)
    return run_seed + SEED_OFFSETS.get(stage, 0)
