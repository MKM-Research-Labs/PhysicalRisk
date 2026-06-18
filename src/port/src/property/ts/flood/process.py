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

"""Property flood processing: orchestrates nearest-gauge selection,
flood propagation, and per-property JSON output."""

import json
from pathlib import Path
from typing import Dict, Optional

from ..encoder import DateTimeEncoder
from .nearest import NearestGaugeMixin
from .propagation import PropagationMixin


class FloodMixin(NearestGaugeMixin, PropagationMixin):
    """Mixin providing flood propagation and property processing methods."""

    @staticmethod
    def _zone_from_offset(offset: float) -> str:
        """Derive EA flood zone from vertical offset above river (metres)."""
        from config.port import EA_FLOOD_ZONE_ELEVATION_BOUNDS
        for zone, (lo, hi) in EA_FLOOD_ZONE_ELEVATION_BOUNDS.items():
            # A None bound is unbounded on that side: Zone 3b (functional
            # floodplain) extends to/below river level (lo=None); Zone 1
            # extends arbitrarily high (hi=None).
            if (lo is None or offset >= lo) and (hi is None or offset < hi):
                return zone
        return 'Zone 1'

    def _process_property(self, prop: Dict, gauge_lookup: Dict,
                           gaugets: Dict, pts_dir: Path,
                           mode: str = "normal") -> Optional[Dict]:
        """Process a single asset: find floods and build hydrographs.

        Reads the asset record under the root section configured by
        ``self.ASSET_CONFIG.root_section_key`` (``PropertyHeader`` for
        residential, ``CommercialAsset`` for commercial).

        Args:
            mode: "normal" (default), "shd" (zero elevation diff),
                  "she" (zero distance), or "bri" (BRI-adjusted floor level —
                  raises the flood threshold by the Building Resilience Index
                  floor credit; distance and elevation stay at their real
                  values).
        """
        cfg = self.ASSET_CONFIG
        ph = prop.get(cfg.root_section_key, {})
        hdr = ph.get('Header', {})
        loc = ph.get('Location', {})
        risk = loc.get('RiskAssessment', ph.get('RiskAssessment', {}))
        construction = ph.get('Construction', {})
        attrs = ph.get(cfg.attributes_key, {})
        ph_risk = ph.get('RiskAssessment', {})

        prop_id = (hdr.get('PropertyID', '')
                   or attrs.get('PropertyID', '')
                   or ph.get(cfg.attributes_key, {}).get('PropertyID', ''))
        prop_lat = loc.get('LatitudeDegrees', 0)
        prop_lon = loc.get('LongitudeDegrees', 0)
        prop_elevation = risk.get('GroundLevelMeters', 0)
        # BRI mode raises the flood threshold to the BRI-adjusted floor level
        # (surveyed floor + resilience credit). Falls back to the surveyed
        # floor when the adjusted value is absent, so the mode is a safe no-op
        # for assets lacking the field. Distance/elevation are untouched —
        # BRI only moves the floor side of the flood test.
        if mode == "bri":
            floor_level = construction.get(
                'BRIAdjustedFloorLevelMeters',
                construction.get('FloorLevelMeters', 0))
        else:
            floor_level = construction.get('FloorLevelMeters', 0)
        terrain_type = loc.get('TerrainType',
                               attrs.get('TerrainType', 'urban'))

        if not prop_id or prop_lat == 0:
            return None

        nearest = self._find_nearest_gauges(prop_lat, prop_lon, gauge_lookup)
        if not nearest:
            return None

        # The synthetic gauge (position [0] when present) is the controlling
        # boundary condition — it represents the river at the property's
        # location.  Use its elevation for all downstream calculations.
        synth = nearest[0] if nearest[0]['gauge_id'].startswith('SYNTH') else None
        controlling_elev = (synth or nearest[0])['gauge_info'].get('elevation', 0)

        # Elevation sanity check: property must be above the controlling gauge.
        if controlling_elev > 0 and prop_elevation < controlling_elev:
            prop_elevation = controlling_elev + 0.5

        # Derive EA flood zone from actual elevation offset above synthetic.
        # This replaces the CDM-assigned zone to ensure consistency between
        # zone classification and the flood simulation's elevation mechanics.
        actual_offset = max(0.0, prop_elevation - controlling_elev)
        flood_zone = self._zone_from_offset(actual_offset)

        # Collect storms that exceeded alert at ANY of the nearest gauges.
        # Alert is the wide net — we process all of these through the
        # propagation model.  The severe count is tracked separately for
        # display in the basis strip.
        alert_storms = {}  # sequence_id -> {gauge_id: response}
        for ng in nearest:
            gid = ng['gauge_id']
            gt = gaugets.get(gid, {})
            responses = gt.get('storm_responses', {}).get('responses', [])
            for resp in responses:
                if resp.get('exceeded_alert', False):
                    sid = resp.get('storm_id', '')
                    seq_id = self._storm_to_sequence.get(sid, sid)
                    if seq_id not in alert_storms:
                        alert_storms[seq_id] = {}
                    existing = alert_storms[seq_id].get(gid)
                    if existing is None or resp.get('peak_level_m', 0) > existing.get('peak_level_m', 0):
                        alert_storms[seq_id][gid] = resp

        floods_at_gauge = len(alert_storms)

        # Count severe separately — this is the PRS trigger count for basis display
        severe_at_gauge = 0
        for seq_id, gauge_resps in alert_storms.items():
            if any(r.get('exceeded_severe', False) for r in gauge_resps.values()):
                severe_at_gauge += 1

        flood_events = []
        for storm_id, gauge_responses in alert_storms.items():
            event = self._compute_property_flood(
                storm_id, gauge_responses, nearest,
                prop_lat, prop_lon, prop_elevation, floor_level,
                gaugets, mode=mode, terrain_type=terrain_type,
            )
            if event:
                # Tag whether the gauge hit severe for this storm
                event['exceeded_severe'] = any(
                    r.get('exceeded_severe', False)
                    for r in gauge_responses.values()
                )
                flood_events.append(event)

        floods_at_property = sum(1 for e in flood_events if e.get('flooded'))

        max_depth = max((e['flood_depth_m'] for e in flood_events), default=0.0)
        max_damage = max((e['damage_ratio'] for e in flood_events), default=0.0)

        summary = {
            'property_id': prop_id,
            'elevation_m': round(prop_elevation, 2),
            'floor_level_m': round(floor_level, 2),
            'nearest_gauges': [
                {
                    'gauge_id': ng['gauge_id'],
                    'distance_m': round(ng['distance_m'], 1),
                }
                for ng in nearest
            ],
            'floods_at_nearest_gauge': floods_at_gauge,
            'severe_at_nearest_gauge': severe_at_gauge,
            'floods_at_property': floods_at_property,
            'gauge_to_property_ratio': round(
                floods_at_property / severe_at_gauge * 100, 1
            ) if severe_at_gauge > 0 else 0.0,
            'max_depth_m': round(max_depth, 4),
            'max_damage_ratio': round(max_damage, 4),
        }

        # Build nearest_gauges with synthetic overrides for output
        output_nearest_gauges = []
        for ng in nearest:
            g_elev = ng['gauge_info']['elevation']
            out_dist = 0.0 if mode == "she" else ng['distance_m']
            out_gauge_elev = g_elev
            out_prop_elev = g_elev if mode == "shd" else prop_elevation
            output_nearest_gauges.append({
                'gauge_id': ng['gauge_id'],
                'distance_m': round(out_dist, 1),
                'gauge_elevation_m': round(out_gauge_elev, 2),
            })

        effective_elevation = prop_elevation
        effective_zone = flood_zone
        if mode == "shd" and nearest:
            # SHD: zero elevation diff — property at gauge level = Zone 3b
            effective_elevation = nearest[0]['gauge_info']['elevation']
            effective_zone = self._zone_from_offset(0.0)
        elif mode == "she":
            # SHE: zero distance — zone stays as derived from real elevation
            pass

        prop_file = pts_dir / f'{prop_id}.json'
        prop_data = {
            'property_id': prop_id,
            'location': {
                'lat': prop_lat,
                'lon': prop_lon,
            },
            'elevation_m': round(effective_elevation, 4),
            'floor_level_m': round(floor_level, 4),
            'flood_zone': effective_zone,
            'terrain_type': terrain_type,
            'property_type': attrs.get(cfg.type_field, cfg.type_default),
            'construction_year': attrs.get('ConstructionYear', 2000),
            'property_period': attrs.get('PropertyPeriod', '2000-2008'),
            'nearest_gauges': output_nearest_gauges,
            'flood_events': flood_events,
            'summary': summary,
        }
        with open(prop_file, 'w') as f:
            json.dump(prop_data, f, indent=2, cls=DateTimeEncoder)

        return {'summary': summary}
