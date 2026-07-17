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

"""
Hand-rolled Sequential Monte Carlo (particle filter) engine.

Drives Phase 1's pure-simulation mode (soft plausibility scores, no real
observations). The ``ParticleFilter`` SMC engine and the
``systematic_resample`` index sampler are re-exported from ``_core``.

Usage:
    rng = np.random.default_rng(seed)
    pf = ParticleFilter(n_particles=1000, config=cfg, rng=rng)
    pf.initialize()
    trajectories = pf.run_to_horizon(horizon_hours=168.0)
"""

from ._core import ParticleFilter, systematic_resample

__all__ = [
    "ParticleFilter",
    "systematic_resample",
]
