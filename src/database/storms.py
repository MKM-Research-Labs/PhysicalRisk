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

"""Public API — storm sequences, stress storms, sequence-gauge summaries, perils."""

from __future__ import annotations

from typing import Iterator

from ._helpers import load_or, records
from .backend import active_backend


# ── Storm sequences ──────────────────────────────────────────────────────────
def get_storm_sequences(catchment):
    return load_or("storm_sequences", catchment)

def storm_sequences_exists(catchment) -> bool:
    """True if storm_sequences.json is present (no parse — corruption-agnostic)."""
    return active_backend().exists("storm_sequences", catchment)

def save_storm_sequences(catchment, payload):
    active_backend().save("storm_sequences", catchment, payload)

def get_sequence_summary(catchment):
    return load_or("sequence_summary", catchment)

def save_sequence_summary(catchment, payload):
    active_backend().save("sequence_summary", catchment, payload)

def get_legacy_storm_sequences(catchment):
    """Pre-sharded single-file storm metadata (``storms.json``); None if absent.

    Read-only fallback for ``storm_sequences.json`` on legacy portfolios."""
    return load_or("storm_sequences_legacy", catchment)


# ── Stress storms (index + per storm) ────────────────────────────────────────
def list_stress_storms(catchment):
    return records(load_or("stress_storm_index", catchment, default=[]))

def get_stress_storm_index(catchment):
    """Raw stress-storm index document (``stress_storms/_index.json``); None if absent.

    Unlike :func:`list_stress_storms`, this preserves exact key access (e.g.
    ``.get('storms', [])``) for callers that need the whole document."""
    return load_or("stress_storm_index", catchment)

def get_legacy_stress_storms(catchment):
    """Pre-sharded single-file stress storms (``stress_storms.json``); None if absent.

    Read-only fallback for the ``stress_storms/_index.json`` document."""
    return load_or("stress_storms_legacy", catchment)

def get_stress_storm(catchment, storm_id):
    return load_or("stress_storm", catchment, storm_id)

def save_stress_storm(catchment, storm_id, payload):
    active_backend().save("stress_storm", catchment, payload, storm_id)


# ── Sequence → gauge summaries ───────────────────────────────────────────────
def list_sequence_gauges(catchment) -> list[str]:
    return list(active_backend().iter_keys("sequence_gauge", catchment))

def get_sequence_gauge(catchment, gauge_id):
    return load_or("sequence_gauge", catchment, gauge_id)

def save_sequence_gauge(catchment, gauge_id, payload):
    active_backend().save("sequence_gauge", catchment, payload, gauge_id)

def clear_sequence_gauges(catchment):
    """Remove every per-gauge sequence summary (replaces an ``rmtree`` of the
    ``sequence_gauge`` collection before a full rewrite)."""
    active_backend().clear("sequence_gauge", catchment)


# ── Typhoon damage events (keyed per event) ──────────────────────────────────
def typhoon_events_exist(catchment) -> bool:
    """True if the typhoon damage collection (``typhoon/damage``) has been generated."""
    return active_backend().has_collection("typhoon_event", catchment)

def get_typhoon_event(catchment, event_id):
    return load_or("typhoon_event", catchment, event_id)

def iter_typhoon_event_ids(catchment) -> Iterator[str]:
    return active_backend().iter_keys("typhoon_event", catchment)

def save_typhoon_event(catchment, event_id, payload):
    active_backend().save("typhoon_event", catchment, payload, event_id)


# ── Perils (fire / seismic) ──────────────────────────────────────────────────
def get_fire_results(catchment):
    return load_or("fire_results", catchment)

def save_fire_results(catchment, payload):
    active_backend().save("fire_results", catchment, payload)

def get_seismic_results(catchment):
    return load_or("seismic_results", catchment)

def save_seismic_results(catchment, payload):
    active_backend().save("seismic_results", catchment, payload)
