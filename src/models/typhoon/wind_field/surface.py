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

"""Surface reduction — spec eq. (29).

Binary land / sea reduction applied at the evaluation point (not the
storm center). Land surfaces reduce sustained winds via increased
friction; sea surfaces are taken as the reference (typical reduction
factor 1.0).

A future phase can replace the binary with a continuous roughness or
land-cover map without changing the calling signature.
"""

__all__ = ["surface_factor"]


def surface_factor(is_land: bool, rho_surf_sea: float, rho_surf_land: float) -> float:
    """Return the surface reduction multiplier rho_surf at the point."""
    return rho_surf_land if is_land else rho_surf_sea
