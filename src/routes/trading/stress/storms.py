# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Stress storms endpoint — list storms that breached alert at a given gauge."""

import logging

from flask import jsonify, request

from .. import trading_bp
from ._helpers import _load_stress_storms, _load_stress_storm

logger = logging.getLogger(__name__)


@trading_bp.route("/trading/stress/storms", methods=["GET"])
def get_stress_storms():
    """Get storms that breached alert at a given gauge.

    If gauge_id is omitted, returns a summary with total storm count only
    (used by the startup preloader to show a stat in the loading popup).
    """
    gauge_id = request.args.get('gauge_id')

    try:
        data = _load_stress_storms()
        if not data:
            return jsonify({"status": "error",
                            "message": "stress_storms not found"}), 404

        # No gauge_id — return total count for startup popup stat
        if not gauge_id:
            all_storms = data.get('storms', [])
            return jsonify({
                'status': 'success',
                'storms': all_storms,
                'count': len(all_storms),
            })

        # Filter index to storms that breached alert at this gauge,
        # then load each storm's full record to get gauge-specific data
        storms = []
        for idx_entry in data.get('storms', []):
            # New index format has gauge_ids_alert; legacy has gauge_responses
            gauge_ids_alert = idx_entry.get('gauge_ids_alert')
            if gauge_ids_alert is not None:
                # New directory-based format — filter by index
                if gauge_id not in gauge_ids_alert:
                    continue
                # Load full storm to get gauge-specific response
                full_storm = _load_stress_storm(idx_entry['storm_id'])
                if not full_storm:
                    continue
            else:
                # Legacy single-file format — storm already has gauge_responses
                full_storm = idx_entry

            # Find this gauge's response
            gauge_resp = None
            for gr in full_storm.get('gauge_responses', []):
                if gr.get('gauge_id') == gauge_id and gr.get('exceeded_alert'):
                    gauge_resp = gr
                    break
            if not gauge_resp:
                continue

            storms.append({
                'storm_id': idx_entry['storm_id'],
                'name': idx_entry.get('name', ''),
                'intensity_category': idx_entry.get('intensity_category', ''),
                'duration_hours': idx_entry.get('duration_hours', 0),
                'peak_position': idx_entry.get('peak_position', 0.5),
                'peak_level_m': gauge_resp.get('peak_level_m', 0),
                'base_level_m': gauge_resp.get('base_level_m', 0),
                'level_change_m': gauge_resp.get('level_change_m', 0),
                'max_trigger': idx_entry.get('trigger_summary', {}).get(
                    'max_trigger', 'alert'),
                'exceeded_warning': gauge_resp.get('exceeded_warning', False),
                'exceeded_severe': gauge_resp.get('exceeded_severe', False),
                'effective_precipitation_mm': idx_entry.get(
                    'effective_precipitation_mm', 0),
                'gauges_severe': idx_entry.get('trigger_summary', {}).get(
                    'gauges_severe', 0),
            })

        # Sort by peak level descending (worst storms first)
        storms.sort(key=lambda x: -x['peak_level_m'])

        return jsonify({
            'status': 'success',
            'gauge_id': gauge_id,
            'storms': storms,
            'count': len(storms),
        })

    except Exception as e:
        logger.error("Stress storms error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500
