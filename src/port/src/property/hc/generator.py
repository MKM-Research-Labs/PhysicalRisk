# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Property-Level Hazard Curve Generator with PRS Pricing and Basis Calculation.

For each property in the propertyts output:
1. Counts severe flood events from the Monte Carlo simulation
2. Computes spread as event_count / num_scenarios (bp)
3. Calculates basis vs synthetic gauge spread
4. Attaches spread decomposition (gauge → SHD → SHE → property)

Usage:
    from port.src.property.hc import PropertyHazardCurveGenerator
    generator = PropertyHazardCurveGenerator(output_dir)
    result = generator.generate()
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union

import numpy as np

from config import config
from models.hazard.terrain_grid import compute_terrain_grid
from port.utils.asset_config import RESIDENTIAL_CONFIG, AssetTypeConfig
from port.utils.generator_base import GeneratorInitMixin

from .constants import MIN_PRS_SPREAD_BPS, TENORS
from .encoder import json_default
from .loader import LoaderMixin
from .pricing import PricingMixin

logger = logging.getLogger(__name__)


class PropertyHazardCurveGenerator(LoaderMixin, PricingMixin, GeneratorInitMixin):
    """
    Property-level hazard curve, PRS pricing, and basis calculator.

    Reads the asset ts output, counts severe flood events, computes
    spread as event_count / num_scenarios, and calculates basis
    against the synthetic gauge.

    Asset-type-specific knobs (input ts dir, output JSON filename, id
    prefix) come from ``ASSET_CONFIG``. Subclass and override that single
    attribute for other asset classes (e.g. commercial).
    """

    ASSET_CONFIG: AssetTypeConfig = RESIDENTIAL_CONFIG

    def __init__(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        verbose: bool = True,
        mode: str = "normal",
    ):
        self._init_generator(output_dir, mode, verbose)

    # Keep as static method on class for backward compatibility with tests
    _json_default = staticmethod(json_default)

    def generate(self) -> Dict:
        """
        Generate property-level hazard curves, PRS pricing, and basis.

        Returns:
            Dictionary with generation metadata and summary statistics.
        """
        cfg = self.ASSET_CONFIG
        pts_subdir = cfg.ts_dirs[self.mode]
        output_filename = cfg.hc_files[self.mode]
        mode_label = f" [{self.mode}]" if self.mode != "normal" else ""
        self.log(f"{cfg.label} Hazard Curve Generator{mode_label}")
        self.log(f"Catchment: {config.CATCHMENT}")

        pts_dir = self.output_dir / pts_subdir
        if not pts_dir.exists():
            raise FileNotFoundError(
                f"{cfg.label} timeseries directory not found: {pts_dir}\n"
                f"Run: python app.py port --{pts_subdir} first"
            )

        property_files = sorted(pts_dir.glob(cfg.id_glob))
        self.log(f"Found {len(property_files)} property timeseries files")

        gauge_hazard, num_storms = self._load_gauge_hazard_curves()
        self.log(f"Loaded hazard curves for {len(gauge_hazard)} gauges ({num_storms} storms)")

        price_prs_func = self._get_prs_pricer()

        results = {}
        stats = {
            'total_properties': len(property_files),
            'properties_processed': 0,
            'properties_skipped': 0,
            'total_flood_events': 0,
            'avg_basis_bps': 0.0,
            'avg_transmission_rate': 0.0,
            'num_storms': num_storms,
        }

        basis_values = []
        transmission_rates = []
        spread_values = []

        for i, pf in enumerate(property_files):
            result = self._process_property(pf, gauge_hazard, price_prs_func, num_storms)
            if result:
                results[result['property_id']] = result
                stats['properties_processed'] += 1
                stats['total_flood_events'] += result['flood_count']

                spread = result.get('term_structure', {}).get(
                    'severe', {}).get('prs_spread_bps', [0])[0]
                spread_values.append(spread)

                if result.get('summary', {}).get('avg_basis_bps') is not None:
                    basis_values.append(result['summary']['avg_basis_bps'])
                if result.get('summary', {}).get('flood_transmission_rate') is not None:
                    transmission_rates.append(result['summary']['flood_transmission_rate'])
            else:
                stats['properties_skipped'] += 1

            if (i + 1) % 50 == 0:
                self.log(f"  Processed {i + 1}/{len(property_files)} properties")

        stats['avg_basis_bps'] = round(np.mean(basis_values), 2) if basis_values else 0.0
        stats['avg_transmission_rate'] = round(np.mean(transmission_rates), 4) if transmission_rates else 0.0
        stats['avg_spread_bps'] = round(np.mean(spread_values), 2) if spread_values else 0.0

        output_path = self.output_dir / output_filename
        output_data = {
            'metadata': {
                'catchment_id': config.CATCHMENT,
                'generated_at': datetime.now().isoformat(),
                'num_properties': len(results),
                'num_storms': num_storms,
                'tenors': TENORS,
                'terrain_grid': compute_terrain_grid(),
            },
            'summary': stats,
            'property_hazard_curves': results,
        }

        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2, default=json_default)

        self.log(f"Output: {output_path.name}")
        avg_spread = stats['avg_spread_bps']
        n_flooded = len([s for s in spread_values if s > 0])
        self.log(f"  {stats['properties_processed']} properties  |  "
                 f"{n_flooded} with floods  |  {stats['properties_processed'] - n_flooded} zero")
        self.log(f"  Avg basis: {stats['avg_basis_bps']:.1f} bps")
        self.log(f"  Avg transmission rate: {stats['avg_transmission_rate']:.1%}")

        return stats

    def attach_spread_decomposition(self) -> int:
        """
        Post-processing: attach spread decompositions to the normal hc file.

        Loads the configured asset-type's normal / shd / she hc files
        (e.g. propertyhc.json / propertyshd.json / propertyshe.json for
        residential; commercialhc.json / commercialshd.json /
        commercialshe.json for commercial) and computes the data-driven
        spread decomposition for each asset.

        Returns:
            Number of assets with decomposition attached.
        """
        cfg = self.ASSET_CONFIG
        hc_path = self.output_dir / cfg.hc_files["normal"]
        shd_path = self.output_dir / cfg.hc_files["shd"]
        she_path = self.output_dir / cfg.hc_files["she"]
        bri_path = self.output_dir / cfg.hc_files["bri"]
        win_path = self.output_dir / cfg.hc_files["win"]
        faw_path = self.output_dir / cfg.hc_files["faw"]
        fow_path = self.output_dir / cfg.hc_files["fow"]

        if not hc_path.exists():
            self.log(f"{hc_path.name} not found — skipping decomposition")
            return 0

        with open(hc_path, 'r') as f:
            hc_data = json.load(f)

        shd_curves = {}
        if shd_path.exists():
            with open(shd_path, 'r') as f:
                shd_curves = json.load(f).get('property_hazard_curves', {})

        she_curves = {}
        if she_path.exists():
            with open(she_path, 'r') as f:
                she_curves = json.load(f).get('property_hazard_curves', {})

        # BRI-adjusted floor curves (the 5th basis step). Absent until the
        # propertybri/commercialbri stage has run — decomposition then simply
        # omits the resilience leg.
        bri_curves = {}
        if bri_path.exists():
            with open(bri_path, 'r') as f:
                bri_curves = json.load(f).get('property_hazard_curves', {})

        # Wind-coupled peril scenario files (win/faw/fow). Each is a full hc
        # produced by the SAME pricer over a re-stamped peril timeseries, so a
        # curve's 'severe' 5yr spread (and its top-level flood_count) ARE the
        # peril spread/count. When present they are the CANONICAL source for the
        # peril-outcomes fan (Option A); absent until the windhazard stage runs
        # (flood-only catchments then fall back to the damage-join prs_perils).
        win_curves, faw_curves, fow_curves = {}, {}, {}
        if win_path.exists():
            with open(win_path, 'r') as f:
                win_curves = json.load(f).get('property_hazard_curves', {})
        if faw_path.exists():
            with open(faw_path, 'r') as f:
                faw_curves = json.load(f).get('property_hazard_curves', {})
        if fow_path.exists():
            with open(fow_path, 'r') as f:
                fow_curves = json.load(f).get('property_hazard_curves', {})

        curves = hc_data.get('property_hazard_curves', {})
        count = 0

        for prop_id, pc in curves.items():
            nearest_gauges = pc.get('nearest_gauges', [])
            synth_gauge = next(
                (ng for ng in nearest_gauges
                 if ng.get('gauge_id', '').startswith('SYNTH-')),
                None
            )

            shd_pc = shd_curves.get(prop_id, {})
            she_pc = she_curves.get(prop_id, {})
            bri_pc = bri_curves.get(prop_id, {})

            prop_spread = self._get_5yr_spread(pc, 'severe')
            shd_spread = self._get_5yr_spread(shd_pc, 'severe')
            she_spread = self._get_5yr_spread(she_pc, 'severe')

            # Gauge spread baseline: use the synthetic gauge's severe spread
            if synth_gauge:
                synth_basis = synth_gauge.get('basis_bps', {}).get(
                    'severe', {}).get('values', [])
                prop_5yr = pc.get('term_structure', {}).get(
                    'severe', {}).get('prs_spread_bps', [0] * 5)
                p5 = prop_5yr[4] if len(prop_5yr) > 4 else 0.0
                sb = synth_basis[4] if len(synth_basis) > 4 else 0.0
                gauge_spread = p5 + sb
            else:
                gauge_spreads = pc.get('idw_gauge_spreads', {}).get('severe', [])
                gauge_spread = gauge_spreads[4] if len(gauge_spreads) > 4 else 0.0

            decomposition = {
                'gauge_spread_bps': round(gauge_spread, 2),
                'property_spread_bps': round(prop_spread, 2),
                'shd_spread_bps': round(shd_spread, 2),
                'she_spread_bps': round(she_spread, 2),
                'distance_first': {
                    'distance_effect_bps': round(she_spread - gauge_spread, 2),
                    'elevation_effect_bps': round(prop_spread - she_spread, 2),
                },
                'elevation_first': {
                    'elevation_effect_bps': round(shd_spread - gauge_spread, 2),
                    'distance_effect_bps': round(prop_spread - shd_spread, 2),
                },
            }

            # BRI-adjusted floor leg (5th basis step: no-BRI → BRI). Raising the
            # floor to the resilience-credited level can only reduce the severe
            # flood spread, so resilience_effect_bps = no-BRI − BRI ≥ 0. Only
            # attached when the asset has a BRI-adjusted curve.
            if prop_id in bri_curves:
                bri_spread = self._get_5yr_spread(bri_pc, 'severe')
                decomposition['bri_spread_bps'] = round(bri_spread, 2)
                decomposition['resilience_effect_bps'] = round(
                    prop_spread - bri_spread, 2)

            # Stage 6 — the four peril outcomes branch at the property/BRI node
            # (flood spine stays geographic; wind is a pure intersect/union with
            # no gauge propagation). Absent for flood-only catchments.
            #
            # Option A (canonical): when the dedicated win/faw/fow scenario files
            # exist, the fan is sourced from THEM — each scenario's 'severe' 5yr
            # spread and top-level flood_count is the peril spread/count. The
            # flood_only leg is the (geographic) flood spine itself.
            win_pc = win_curves.get(prop_id, {})
            faw_pc = faw_curves.get(prop_id, {})
            fow_pc = fow_curves.get(prop_id, {})
            if win_pc or faw_pc or fow_pc:
                win_spread = self._get_5yr_spread(win_pc, 'severe')
                faw_spread = self._get_5yr_spread(faw_pc, 'severe')
                fow_spread = self._get_5yr_spread(fow_pc, 'severe')
                decomposition['win_spread_bps'] = round(win_spread, 2)
                decomposition['faw_spread_bps'] = round(faw_spread, 2)
                decomposition['fow_spread_bps'] = round(fow_spread, 2)
                decomposition['peril_outcomes'] = {
                    'flood_only': {
                        'count': pc.get('flood_count', 0),
                        'spread_bps': round(prop_spread, 2)},
                    'wind_only': {
                        'count': win_pc.get('flood_count', 0),
                        'spread_bps': round(win_spread, 2)},
                    'flood_or_wind': {
                        'count': fow_pc.get('flood_count', 0),
                        'spread_bps': round(fow_spread, 2)},
                    'flood_and_wind': {
                        'count': faw_pc.get('flood_count', 0),
                        'spread_bps': round(faw_spread, 2)},
                    'source': 'scenario_files',
                }
            else:
                # Fallback: damage-join prs_perils (no scenario files on disk).
                # Prefer the BRI-adjusted node when present (the level the book
                # actually trades at), else the property node.
                peril_outcomes = bri_pc.get('prs_perils') or pc.get('prs_perils')
                if peril_outcomes:
                    decomposition['peril_outcomes'] = peril_outcomes

            pc['spread_decomposition'] = decomposition
            count += 1

        with open(hc_path, 'w') as f:
            json.dump(hc_data, f, indent=2, default=json_default)

        self.log(f"Spread decomposition attached to {count} properties")
        return count

    @staticmethod
    def _get_5yr_spread(pc: Dict, threshold: str = 'any_flood') -> float:
        """Extract 5yr PRS spread for a given threshold from a hazard curve dict."""
        ts = pc.get('term_structure', {})
        spreads = ts.get(threshold, {}).get('prs_spread_bps', [])
        return spreads[4] if len(spreads) > 4 else 0.0
