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

"""Public API — trading desk (PRS trades, marks, market state, EOD)."""

from __future__ import annotations

from config.data_layout import EOD_KEY_PREFIX

from .backend import active_backend
from ._helpers import load_or


def _eod_key(eod_date: str) -> str:
    return f"{EOD_KEY_PREFIX}{eod_date.replace('-', '')}"


# ── PRS trades ───────────────────────────────────────────────────────────────
def list_prs_trades(catchment) -> list:
    repo = active_backend()
    return [repo.load("prs_trade", catchment, k) for k in repo.iter_keys("prs_trade", catchment)]

def iter_prs_trade_ids(catchment):
    """Swap ids of every PRS trade. Lets callers load each defensively (skip a
    corrupt record) rather than eagerly as :func:`list_prs_trades` does."""
    return active_backend().iter_keys("prs_trade", catchment)

def get_prs_trade(catchment, swap_id):
    return load_or("prs_trade", catchment, swap_id)

def commit_prs_trade(catchment, trade):       # -> @require("Func003", "create")
    active_backend().save("prs_trade", catchment, trade, trade["swap_id"])

def save_prs_trade(catchment, swap_id, trade):
    """Persist an updated PRS trade record under an explicit swap id (e.g. a
    close-out rewrite), where the id is not the record's own ``swap_id`` field."""
    active_backend().save("prs_trade", catchment, trade, swap_id)


# ── Trade marks / status ─────────────────────────────────────────────────────
def get_trade_marks(catchment) -> dict:
    return load_or("trade_marks", catchment, default={})

def save_trade_marks(catchment, marks):
    active_backend().save("trade_marks", catchment, marks)

def set_trade_status(catchment, swap_id, status):   # -> @require("Func003", "write")
    marks = get_trade_marks(catchment)
    marks[swap_id] = {"trade_status": status}
    save_trade_marks(catchment, marks)


# ── Market state ─────────────────────────────────────────────────────────────
def get_market_state(catchment):
    return load_or("market_state", catchment)

def save_market_state(catchment, state):
    active_backend().save("market_state", catchment, state)


# ── End-of-day snapshots ─────────────────────────────────────────────────────
def list_eod_snapshots(catchment) -> list[str]:
    return list(active_backend().iter_keys("eod_snapshot", catchment))

def iter_eod_snapshots(catchment) -> list:
    """All EOD snapshot documents, in chronological (sorted-key) order."""
    repo = active_backend()
    return [repo.load("eod_snapshot", catchment, k)
            for k in repo.iter_keys("eod_snapshot", catchment)]

def get_eod_snapshot(catchment, eod_date):
    return load_or("eod_snapshot", catchment, _eod_key(eod_date))

def save_eod_snapshot(catchment, eod_date, payload):
    active_backend().save("eod_snapshot", catchment, payload, _eod_key(eod_date))
