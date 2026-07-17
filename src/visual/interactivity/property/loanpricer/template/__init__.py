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

"""Loan Pricer JS/HTML template (assembled).

The client-side body is held as a ``str.format`` template with the
placeholders ``{panel_width}`` / ``{panel_height}``. It was split into
4 byte-exact parts to keep every file under the 300-line limit;
they are concatenated here into the original constant.
"""

from ._part1 import PART as _P1
from ._part2 import PART as _P2
from ._part3 import PART as _P3
from ._part4 import PART as _P4

LOAN_PRICER_JS_TEMPLATE = _P1 + _P2 + _P3 + _P4

__all__ = ["LOAN_PRICER_JS_TEMPLATE"]
