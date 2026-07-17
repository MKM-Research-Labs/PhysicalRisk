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
BRI fire-resilience credit model.

A discrete-time Bayesian fire-progression engine designed to sit pari-passu
with the 10,000-storm Monte Carlo engine so fire loss aggregates into the same
resilience-credit currency.

Stage 1 (this module set) implements Model A — Poisson initiation: per asset,
draw n_sim Poisson counts and decide fire / no-fire, then assign an initiation
(entry-point) class to each instantiated fire. Later stages run the 15-min,
200-step progression to the point of no return.

Configuration types come from config.fire; all numeric seeds come from
config/fire_matrices.json. The model layer embeds no numbers.
"""
