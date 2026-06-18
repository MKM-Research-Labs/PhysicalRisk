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

"""Typhoon stage input loaders and severity-quantile helper."""

import importlib

from ...context import StageContext


def _load_catchment_typhoon_config(catchment_id: str):
    """Look up data/catch/<catchment_id>/tc.py and build a CatchmentTyphoonConfig.

    The catchment file is expected to expose a build_typhoon_config()
    function returning the assembled config. A catchment without typhoon
    coverage (e.g. Thames, extratropical) is rejected with a clear error
    so the user can pick a different flag or a different catchment.
    """
    try:
        module = importlib.import_module(f"catch.{catchment_id}.tc")
    except ModuleNotFoundError as exc:
        raise SystemExit(
            f"No typhoon configuration found for catchment '{catchment_id}'. "
            f"Expected file: data/catch/{catchment_id}/tc.py. "
            f"--typhoon is only valid for catchments with tropical-cyclone exposure."
        ) from exc

    builder = getattr(module, "build_typhoon_config", None)
    if builder is None:
        raise SystemExit(
            f"data/catch/{catchment_id}/tc.py must expose build_typhoon_config(). "
            f"See data/catch/halong/tc.py for the reference layout."
        )
    return builder(catchment_id=catchment_id)


def _severity_quantiles(z_values: list) -> list:
    """Map per-event severity latents z to empirical quantiles q_i.

    ``q_i = rank(z_i) / (N+1)`` using average ranks for ties (coupling_spec.md
    §3). The (N+1) denominator keeps every q strictly inside (0, 1) so the §4
    inverse-survival map ``Vmax = S_cat⁻¹(1−ρ_w)`` never hits the degenerate
    endpoints. Returns a list aligned 1:1 with the input order.
    """
    from scipy.stats import rankdata

    if not z_values:
        return []
    n = len(z_values)
    ranks = rankdata(z_values, method="average")
    return [float(r / (n + 1)) for r in ranks]


def _load_storm_event_drivers(ctx: StageContext) -> list:
    """Read storm_sequences.json and return the per-event coupling drivers.

    Each driver is ``{"event_id", "base_intensity", "seed"}`` in file order —
    the 1:1 storm<->typhoon pairing produced by the storm stage (Stage 2).
    ``base_intensity`` is the severity latent ``z`` that Stage 3 will use to
    condition typhoon genesis; ``seed`` makes that genesis reproducible per
    event.

    Returns an empty list when storm_sequences.json is missing or carries no
    coupling fields (a pre-Stage-2 file). The caller then falls back to the
    standalone ``--num-typhoon-events`` count.
    """
    import json

    seq_path = ctx.input_dir / "storm_sequences.json"
    if not seq_path.exists():
        return []
    try:
        data = json.loads(seq_path.read_text())
    except (OSError, json.JSONDecodeError):
        return []

    drivers = []
    for seq in data.get("sequences", []):
        event_id = seq.get("event_id")
        if not event_id:
            # Pre-coupling file (no event_id) — cannot pair; bail out so the
            # caller uses the standalone count rather than a partial pairing.
            return []
        drivers.append({
            "event_id": event_id,
            "base_intensity": float(seq.get("base_intensity", 0.0)),
            "seed": int(seq.get("seed", 0)),
        })
    return drivers


def _load_property_portfolio(ctx: StageContext) -> list:
    """Read property.json + commercial.json (when present) for the active catchment.

    Returns a list of property records. Commercial records are appended after
    residential. Missing files are tolerated — the damage step skips when the
    portfolio is empty.
    """
    import json

    portfolio: list = []

    for fname in ("property.json", "commercial.json"):
        path = ctx.input_dir / fname
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, list):
            portfolio.extend(data)
        elif isinstance(data, dict):
            # Common wrappers: {"properties": [...]} or {"Properties": [...]}.
            # commercial.json wraps its records under "commercial_assets".
            for key in ("properties", "Properties", "commercial", "Commercial",
                        "commercial_assets", "CommercialAssets"):
                if isinstance(data.get(key), list):
                    portfolio.extend(data[key])
                    break
    return portfolio
