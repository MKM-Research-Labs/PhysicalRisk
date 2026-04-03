# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Data loading mixin for PropertyHazardCurveGenerator."""

import json
from typing import Dict


class LoaderMixin:
    """Mixin providing data-loading helpers."""

    def _load_gauge_hazard_curves(self) -> tuple:
        """Load gauge hazard curves and sequence count.

        Returns (hazard_curves_dict, num_sequences).  The denominator for
        property base-rate must be the number of *sequences* (the unit of
        risk), not the number of individual storm pulses stored in
        gaugehc.json ``num_storms``.
        """
        hc_path = self.output_dir / 'gaugehc.json'
        if not hc_path.exists():
            self.log("  Warning: gaugehc.json not found, basis will be empty")
            return {}, 1000

        with open(hc_path, 'r') as f:
            data = json.load(f)

        # Sequence count is the correct denominator for property pricing.
        # storm_sequences.json holds the authoritative count.
        seq_path = self.output_dir / 'storm_sequences.json'
        if seq_path.exists():
            with open(seq_path, 'r') as f:
                seq_data = json.load(f)
            num_sequences = seq_data.get('num_sequences', len(seq_data.get('sequences', [])))
        else:
            # Fallback: gaugehc num_storms (may overcount if multi-pulse)
            num_sequences = data.get('metadata', {}).get('num_storms', 1000)
            self.log("  Warning: storm_sequences.json not found, using gaugehc num_storms as fallback")

        hazard_curves = data.get('hazard_curves', {})

        # Enrich each gauge with its severe event count from sequence_gauge/.
        # This gives the true Monte Carlo count rather than the GEV-derived
        # probability in gaugehc.
        seq_gauge_dir = self.output_dir / 'sequence_gauge'
        if seq_gauge_dir.exists():
            for gid in hazard_curves:
                sg_path = seq_gauge_dir / f'{gid}.json'
                if sg_path.exists():
                    with open(sg_path, 'r') as f:
                        sg = json.load(f)
                    seqs = sg.get('sequences', [])
                    severe_count = sum(1 for s in seqs if s.get('severe'))
                    hazard_curves[gid]['severe_event_count'] = severe_count

        return hazard_curves, num_sequences

    def _get_prs_pricer(self):
        """Try to import QuantLib PRS pricer. Returns None if unavailable."""
        try:
            from models.prs.prshc import price_prs
            return price_prs
        except ImportError:
            self.log("  Warning: QuantLib not available, PRS pricing will use analytical model")
            return None
