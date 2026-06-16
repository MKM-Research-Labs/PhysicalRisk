# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Peril timeseries generator (win / faw / fow / bow / baw scenario inputs).

The flood spine writes a per-asset timeseries directory (``propertyts`` /
``commercialts``) whose ``flood_events`` carry ``flooded`` + ``exceeded_severe``
flags. The hazard-curve generator counts a PRS trigger as
``is_prs_flood(e) == flooded AND exceeded_severe`` and prices
``count / num_storms × 10 000`` bps.

The wind-coupled scenarios reuse that EXACT pricing path. We do not
re-implement counting — instead we derive new timeseries directories from a
flood-base ts, re-stamping each event's ``flooded`` + ``exceeded_severe`` so the
peril of interest is what the generator counts:

* ``win`` (wind-only)      — flag set iff the paired typhoon's wind triggers
                             :func:`is_prs_wind` for this asset/event.
* ``faw`` (flood AND wind) — flag set iff the event triggers BOTH flood and
                             wind (the joint / intersection leg).
* ``fow`` (flood OR wind)  — flag set iff the event triggers EITHER (union).
* ``bow`` (BRI OR wind)    — like ``fow`` but the flood leg is the BRI-resilient
                             flood (derived from the ``bri`` ts, not ``normal``).
* ``baw`` (BRI AND wind)   — like ``faw`` but anchored on the BRI flood.

``win``/``faw``/``fow`` derive from the RAW flood spine (``normal`` ts); the
flood trigger is the asset's own flood. ``bow``/``baw`` derive from the
BRI-adjusted ts (``bri``) — the BRI mode re-stamps ``flooded``/
``exceeded_severe`` at the resilience-credited floor, so ``is_prs_flood(e)``
read off that ts already IS the BRI-resilient flood trigger. ``bow``/``baw``
are skipped when the ``bri`` ts is absent.

The join contract matches :meth:`PricingMixin._wind_union`: a flood event is
keyed by ``storm_id`` (== ``sequence_id``); ``storm_sequences.json`` maps that
sequence to the paired typhoon ``event_id``; the wind damage rows in
``typhoon/damage/EVT-*.json`` are keyed by that ``event_id`` (filename stem,
which is canonical — the internal ``event_id`` field can be mis-stamped by
genesis). The denominator (``num_storms``) is preserved because we re-stamp
the existing per-storm events in place rather than inventing new ones.

A catchment with no typhoon damage produces empty peril dirs and the wind
hazard stage is skipped — flood-only output is untouched.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Union

from models.floodrisk.depth_damage import is_prs_flood
from models.winddamage.threshold import is_prs_wind

from port.utils.asset_config import RESIDENTIAL_CONFIG, AssetTypeConfig

logger = logging.getLogger(__name__)

# The peril scenarios this generator produces, in their canonical order.
PERIL_MODES = ("win", "faw", "fow", "bow", "baw")

# Each peril mode's flood-base ts: win/faw/fow use the raw flood spine; the
# BRI-anchored bow/baw read the BRI-resilient ts so is_prs_flood off the base
# is already the BRI floor trigger.
PERIL_BASE_MODE = {
    "win": "normal",
    "faw": "normal",
    "fow": "normal",
    "bow": "bri",
    "baw": "bri",
}


class PerilTimeseriesGenerator:
    """Derive win/faw/fow timeseries dirs from the flood spine + typhoon damage.

    Asset-type-specific knobs (base ts dir, peril ts dirs, id glob) come from
    ``ASSET_CONFIG``. Subclass and override that attribute for other asset
    classes, mirroring the hazard-curve generators.
    """

    ASSET_CONFIG: AssetTypeConfig = RESIDENTIAL_CONFIG

    def __init__(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        verbose: bool = True,
    ):
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.verbose = verbose
        self._wind_damage_cache: Optional[Dict[str, Dict[str, Dict]]] = None
        self._seq_to_event_cache: Optional[Dict[str, str]] = None

    def log(self, msg: str):
        if self.verbose:
            logger.info(msg)

    # ------------------------------------------------------------------
    # Join inputs (mirror PricingMixin so the counts agree exactly)
    # ------------------------------------------------------------------

    def _wind_damage_index(self) -> Dict[str, Dict[str, Dict]]:
        """``event_id → {property_id → {peak_sustained_ms, threshold_ms, v_50_eff_ms}}``.

        Walks ``typhoon/damage/EVT-*.json`` once (keyed on the filename stem —
        the canonical event id) and caches the result. Empty when the typhoon
        stage hasn't run for this catchment.
        """
        if self._wind_damage_cache is not None:
            return self._wind_damage_cache
        out: Dict[str, Dict[str, Dict]] = {}
        damage_dir = self.output_dir / 'typhoon' / 'damage'
        if damage_dir.exists():
            for fp in sorted(damage_dir.glob('EVT-*.json')):
                try:
                    with open(fp, 'r') as f:
                        data = json.load(f)
                except (OSError, json.JSONDecodeError):
                    continue
                eid = fp.stem
                pmap: Dict[str, Dict] = {}
                for d in data.get('damages', []):
                    pid = d.get('property_id')
                    if pid:
                        pmap[pid] = {
                            'peak_sustained_ms': d.get('peak_sustained_ms'),
                            'threshold_ms': d.get('threshold_ms'),
                            'v_50_eff_ms': d.get('v_50_eff_ms'),
                        }
                if pmap:
                    out[eid] = pmap
        self._wind_damage_cache = out
        return out

    def _seq_to_event_map(self) -> Dict[str, str]:
        """``sequence_id → event_id`` from ``storm_sequences.json`` (cached)."""
        if self._seq_to_event_cache is not None:
            return self._seq_to_event_cache
        out: Dict[str, str] = {}
        seq_path = self.output_dir / 'storm_sequences.json'
        if seq_path.exists():
            try:
                with open(seq_path, 'r') as f:
                    data = json.load(f)
                for seq in data.get('sequences', []):
                    sid = seq.get('sequence_id')
                    eid = seq.get('event_id')
                    if sid and eid:
                        out[sid] = eid
            except (OSError, json.JSONDecodeError):
                pass
        self._seq_to_event_cache = out
        return out

    # ------------------------------------------------------------------
    # Derivation
    # ------------------------------------------------------------------

    def _peril_flag(self, mode: str, flood_trig: bool, wind_trig: bool) -> bool:
        """Map (flood, wind) triggers to the scenario's PRS trigger.

        For bow/baw the ``flood_trig`` passed in is the BRI-resilient flood
        (the base ts is the bri ts), so the OR/AND logic is identical to
        fow/faw — only the flood anchor differs.
        """
        if mode == "win":
            return wind_trig
        if mode in ("faw", "baw"):
            return flood_trig and wind_trig
        if mode in ("fow", "bow"):
            return flood_trig or wind_trig
        raise ValueError(f"unknown peril mode: {mode!r}")

    def generate(self) -> Dict:
        """Build the win/faw/fow timeseries dirs for this asset type.

        Returns a summary dict; ``available`` is False (and no dirs written)
        when there is no typhoon damage to couple against.
        """
        cfg = self.ASSET_CONFIG
        wind_index = self._wind_damage_index()
        if not wind_index:
            self.log(f"{cfg.label}: no typhoon damage found — peril ts skipped")
            return {"available": False, "label": cfg.label, "modes": {}}

        seq_to_event = self._seq_to_event_map()

        normal_dir = self.output_dir / cfg.ts_dirs["normal"]
        if not normal_dir.exists():
            raise FileNotFoundError(
                f"{cfg.label} base timeseries directory not found: {normal_dir}\n"
                f"Run the flood timeseries stage first."
            )

        mode_stats: Dict[str, Dict] = {}
        for mode in PERIL_MODES:
            base_mode = PERIL_BASE_MODE[mode]
            base_dir = self.output_dir / cfg.ts_dirs[base_mode]
            if not base_dir.exists():
                # bow/baw need the BRI ts; skip silently when it hasn't run
                # (the flood-only / pre-BRI portfolio keeps its layout).
                self.log(
                    f"{cfg.label} [{mode}]: base ts {base_dir.name} absent — skipped"
                )
                continue
            base_files = sorted(base_dir.glob(cfg.id_glob))
            out_dir = self.output_dir / cfg.ts_dirs[mode]
            out_dir.mkdir(parents=True, exist_ok=True)

            # Remove stale per-asset files from a previous (possibly larger)
            # run so a smaller portfolio doesn't leave leftovers that the
            # hazard-curve stage would glob (it globs this dir directly).
            for stale in out_dir.glob(cfg.id_glob):
                stale.unlink()

            triggers = 0
            assets_with_trigger = 0

            for pf in base_files:
                with open(pf, 'r') as f:
                    pdata = json.load(f)

                prop_id = pdata.get('property_id')
                events = pdata.get('flood_events', [])
                asset_hit = False

                for e in events:
                    flood_trig = is_prs_flood(e)
                    eid = seq_to_event.get(e.get('storm_id', ''))
                    wind_row = wind_index.get(eid, {}).get(prop_id) if eid else None
                    wind_trig = is_prs_wind(wind_row) if wind_row else False

                    peril = self._peril_flag(mode, flood_trig, wind_trig)
                    # Re-stamp so the existing pricer counts this peril:
                    # is_prs_flood(e) == flooded AND exceeded_severe.
                    e['flooded'] = peril
                    e['exceeded_severe'] = peril
                    if peril:
                        triggers += 1
                        asset_hit = True

                if asset_hit:
                    assets_with_trigger += 1

                with open(out_dir / pf.name, 'w') as f:
                    json.dump(pdata, f, indent=2)

            mode_stats[mode] = {
                "dir": cfg.ts_dirs[mode],
                "files": len(base_files),
                "triggers": triggers,
                "assets_with_trigger": assets_with_trigger,
            }
            self.log(
                f"{cfg.label} [{mode}]: {len(base_files)} files, "
                f"{triggers} triggers across {assets_with_trigger} assets"
            )

        return {"available": True, "label": cfg.label, "modes": mode_stats}
