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
