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

"""Tests for portfolio-generation seeding.

Reproducibility matters most for a throwaway portfolio: if a run cannot be
reproduced from its command, a failure against generated data cannot be
investigated.
"""

import pytest

from config.port import LEGACY_SEEDS, SEED_OFFSETS, stage_seed


class TestStageSeed:
    @pytest.mark.parametrize("stage,expected", sorted(LEGACY_SEEDS.items()))
    def test_no_run_seed_keeps_the_legacy_value(self, stage, expected):
        """A run without --seed must generate exactly what it did before the
        flag existed, or every stored portfolio silently becomes unreproducible."""
        assert stage_seed(None, stage) == expected

    @pytest.mark.parametrize("stage", ["typhoon", "fire", "seismic"])
    def test_no_run_seed_leaves_unseeded_stages_alone(self, stage):
        """These document "None = nondeterministic"; --seed must be opt-in."""
        assert stage_seed(None, stage) is None

    def test_run_seed_derives_every_stage(self):
        seeds = {s: stage_seed(100, s) for s in SEED_OFFSETS}
        assert all(isinstance(v, int) for v in seeds.values())
        assert seeds["stressm"] == 100  # offset 0

    def test_stages_do_not_share_a_stream(self):
        """Two stages on the same seed would draw the same values — correlated
        randomness that looks like data rather than a bug."""
        seeds = [stage_seed(7, s) for s in SEED_OFFSETS]
        assert len(set(seeds)) == len(seeds)

    def test_same_run_seed_is_stable(self):
        assert [stage_seed(5, s) for s in SEED_OFFSETS] == \
               [stage_seed(5, s) for s in SEED_OFFSETS]

    def test_different_run_seeds_differ(self):
        assert stage_seed(1, "book") != stage_seed(2, "book")

    def test_unknown_stage_falls_back_to_the_run_seed(self):
        assert stage_seed(9, "not-a-stage") == 9
        assert stage_seed(None, "not-a-stage") is None


class TestPerStageOverride:
    """The orchestrator fills per-stage seeds from the run seed, but must never
    overrule one the caller named."""

    @staticmethod
    def _fill(args):
        for stage, attr in (('typhoon', 'typhoon_seed'),
                            ('fire', 'fire_seed'),
                            ('seismic', 'seismic_seed')):
            if getattr(args, attr, None) is None:
                setattr(args, attr, stage_seed(getattr(args, 'seed', None), stage))
        return args

    def test_run_seed_fills_absent_stage_seeds(self):
        from types import SimpleNamespace
        args = self._fill(SimpleNamespace(
            seed=50, typhoon_seed=None, fire_seed=None, seismic_seed=None))
        assert args.typhoon_seed == stage_seed(50, 'typhoon')
        assert args.fire_seed == stage_seed(50, 'fire')

    def test_explicit_stage_seed_survives(self):
        from types import SimpleNamespace
        args = self._fill(SimpleNamespace(
            seed=50, typhoon_seed=999, fire_seed=None, seismic_seed=None))
        assert args.typhoon_seed == 999, "an explicit --typhoon-seed was overruled"
        assert args.fire_seed == stage_seed(50, 'fire')

    def test_no_run_seed_leaves_them_none(self):
        from types import SimpleNamespace
        args = self._fill(SimpleNamespace(
            seed=None, typhoon_seed=None, fire_seed=None, seismic_seed=None))
        assert (args.typhoon_seed, args.fire_seed, args.seismic_seed) == \
               (None, None, None)
