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

from .backend import active_backend
from ._helpers import load_or, records


# ── Storm sequences ──────────────────────────────────────────────────────────
def get_storm_sequences(catchment):
    return load_or("storm_sequences", catchment)

def save_storm_sequences(catchment, payload):
    active_backend().save("storm_sequences", catchment, payload)


# ── Stress storms (index + per storm) ────────────────────────────────────────
def list_stress_storms(catchment):
    return records(load_or("stress_storm_index", catchment, default=[]))

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


# ── Perils (fire / seismic) ──────────────────────────────────────────────────
def get_fire_results(catchment):
    return load_or("fire_results", catchment)

def save_fire_results(catchment, payload):
    active_backend().save("fire_results", catchment, payload)

def get_seismic_results(catchment):
    return load_or("seismic_results", catchment)

def save_seismic_results(catchment, payload):
    active_backend().save("seismic_results", catchment, payload)
