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

"""Spread decomposition post-processing for the hazard curve generator."""

from typing import Dict

import database


class _DecompositionMixin:
    def attach_spread_decomposition(self) -> int:
        """
        Post-processing: attach spread decompositions to the normal hc curves.

        Loads the configured asset-type's normal / shd / she hazard curves
        (propertyhc / propertyshd / propertyshe for residential; the commercial
        equivalents for commercial) through the database seam and computes the
        data-driven spread decomposition for each asset.

        Returns:
            Number of assets with decomposition attached.
        """
        cfg = self.ASSET_CONFIG
        catchment = database.active_catchment()

        def _curves(mode):
            """Hazard-curve dict for *mode* via the seam (empty if absent)."""
            return (cfg.get_hazard_curves(catchment, mode) or {}).get(
                'property_hazard_curves', {})

        hc_data = cfg.get_hazard_curves(catchment, "normal")
        if not hc_data:
            self.log(f"{cfg.hc_files['normal']} not found — skipping decomposition")
            return 0

        shd_curves = _curves("shd")
        she_curves = _curves("she")

        # BRI-adjusted floor curves (the 5th basis step). Absent until the
        # propertybri/commercialbri stage has run — decomposition then simply
        # omits the resilience leg.
        bri_curves = _curves("bri")

        # Wind-coupled peril scenario curves (win/faw/fow). Each is a full hc
        # produced by the SAME pricer over a re-stamped peril timeseries, so a
        # curve's 'severe' 5yr spread (and its top-level flood_count) ARE the
        # peril spread/count. When present they are the CANONICAL source for the
        # peril-outcomes fan (Option A); absent until the windhazard stage runs
        # (flood-only catchments then fall back to the damage-join prs_perils).
        win_curves = _curves("win")
        faw_curves = _curves("faw")
        fow_curves = _curves("fow")

        # BRI-anchored peril scenarios (bow = BRI OR wind, baw = BRI AND wind).
        # Same Option-A protocol as win/faw/fow, but the flood leg is the
        # BRI-resilient flood (the level the book trades at) rather than the raw
        # asset flood. Absent until the bow/baw windhazard sub-stages run.
        bow_curves = _curves("bow")
        baw_curves = _curves("baw")

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

                # BRI-anchored peril legs (bow = BRI OR wind, baw = BRI AND
                # wind). Same scenario protocol; the flood leg is the
                # BRI-resilient flood. Only attached when the bow/baw scenario
                # files exist (else the four raw-flood legs stand alone).
                bow_pc = bow_curves.get(prop_id, {})
                baw_pc = baw_curves.get(prop_id, {})
                if bow_pc or baw_pc:
                    bow_spread = self._get_5yr_spread(bow_pc, 'severe')
                    baw_spread = self._get_5yr_spread(baw_pc, 'severe')
                    decomposition['bow_spread_bps'] = round(bow_spread, 2)
                    decomposition['baw_spread_bps'] = round(baw_spread, 2)
                    decomposition['peril_outcomes']['bri_or_wind'] = {
                        'count': bow_pc.get('flood_count', 0),
                        'spread_bps': round(bow_spread, 2)}
                    decomposition['peril_outcomes']['bri_and_wind'] = {
                        'count': baw_pc.get('flood_count', 0),
                        'spread_bps': round(baw_spread, 2)}
            else:
                # Fallback: damage-join prs_perils (no scenario files on disk).
                # Prefer the BRI-adjusted node when present (the level the book
                # actually trades at), else the property node.
                peril_outcomes = bri_pc.get('prs_perils') or pc.get('prs_perils')
                if peril_outcomes:
                    decomposition['peril_outcomes'] = peril_outcomes

            pc['spread_decomposition'] = decomposition
            count += 1

        cfg.save_hazard_curves(catchment, hc_data, "normal")

        self.log(f"Spread decomposition attached to {count} properties")
        return count

    @staticmethod
    def _get_5yr_spread(pc: Dict, threshold: str = 'any_flood') -> float:
        """Extract 5yr PRS spread for a given threshold from a hazard curve dict."""
        ts = pc.get('term_structure', {})
        spreads = ts.get(threshold, {}).get('prs_spread_bps', [])
        return spreads[4] if len(spreads) > 4 else 0.0
