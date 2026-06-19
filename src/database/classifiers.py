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

"""Public API — classifiers (binary GBM models, one per gauge)."""

from __future__ import annotations

from .backend import active_backend


def list_classifier_ids(catchment) -> list[str]:
    return list(active_backend().iter_keys("classifier", catchment))


def get_classifier(catchment, gauge_id) -> bytes | None:
    try:
        return active_backend().load("classifier", catchment, gauge_id)
    except (FileNotFoundError, KeyError):
        return None


def save_classifier(catchment, gauge_id, blob: bytes):   # -> @require("Func004", "create")
    active_backend().save("classifier", catchment, blob, gauge_id)


def delete_classifier(catchment, gauge_id):              # -> @require("Func004", "delete")
    active_backend().delete("classifier", catchment, gauge_id)
