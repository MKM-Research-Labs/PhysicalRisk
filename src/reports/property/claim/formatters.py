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

"""Formatting utilities shared across claim report pages."""

from reportlab.lib import colors


def fmt_gbp(value: float) -> str:
    """Format a numeric value as a GBP currency string (e.g. £1,234)."""
    try:
        return f'\xa3{float(value):,.0f}'
    except (TypeError, ValueError):
        return str(value)


def seq_type_color(seq_type: str):
    """Return a reportlab Color for a given sequence type label."""
    mapping = {
        'isolated':  colors.lightblue,
        'doublet':   colors.lightyellow,
        'cluster':   colors.lightsalmon,
        'persistent': colors.mistyrose,
    }
    return mapping.get((seq_type or '').lower(), colors.white)
