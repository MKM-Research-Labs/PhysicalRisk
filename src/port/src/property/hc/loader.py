# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Data loading mixin for PropertyHazardCurveGenerator."""

import database


class LoaderMixin:
    """Mixin providing data-loading helpers."""

    def _load_event_frame(self, catchment):
        """Load the storm sequences and derive the hours-clause event frame.

        Lives here rather than on the generator because both the property and
        commercial generators inherit this mixin, and both price off the same
        event structure.

        Args:
            catchment: catchment identifier.

        Returns:
            ``(frame, lambda_per_year)``, or ``(None, 0.0)`` when the sequences
            are unavailable — the caller then prices on the pre-frequency
            metric rather than failing.
        """
        from config.frequency import catchment_lambda
        from models.frequency import build_event_frame
        from models.hazard.io import load_storms_from_sequences

        try:
            sequences = database.get_storm_sequences(catchment)
        except (OSError, ValueError, KeyError):
            return None, 0.0
        if not sequences:
            return None, 0.0
        storms = load_storms_from_sequences(sequences)
        if not storms:
            return None, 0.0
        return build_event_frame(storms), catchment_lambda(catchment)

    def _load_asset_values(self, catchment) -> dict:
        """Return ``{asset_id: reinstatement_value}`` for the loss uplift.

        Reads the portfolio through the seam and pulls each asset's value from
        ``<root_section_key>.Valuation.PropertyValue`` — ``PropertyHeader`` for
        residential, ``CommercialAsset`` for commercial, both supplied by
        ``ASSET_CONFIG`` so the one reader serves both types. An unreadable
        portfolio yields an empty lookup, which prices every asset's loss at a
        value of zero rather than aborting; the missing values surface as
        ``exposure_value = 0`` on each block.

        Args:
            catchment: catchment identifier.

        Returns:
            Mapping of asset identifier to its value.
        """
        section = self.ASSET_CONFIG.root_section_key
        values = {}
        try:
            portfolio = self.ASSET_CONFIG.get_portfolio(catchment)
        except (OSError, ValueError, KeyError):
            return values
        for record in portfolio:
            root = record.get(section, {}) or {}
            asset_id = root.get('Header', {}).get('PropertyID', '')
            if asset_id:
                values[asset_id] = float(
                    root.get('Valuation', {}).get('PropertyValue', 0) or 0)
        return values

    def _load_gauge_hazard_curves(self) -> tuple:
        """Load gauge hazard curves and sequence count through the database seam.

        Returns (hazard_curves_dict, num_sequences).  The denominator for
        property base-rate must be the number of *sequences* (the unit of
        risk), not the number of individual storm pulses stored in the gauge
        hazard curves' ``num_storms``.
        """
        catchment = database.active_catchment()
        data = database.get_gauge_hazard_curves(catchment)
        if not data:
            self.log("  Warning: gauge hazard curves not found, basis will be empty")
            return {}, 1000

        # Sequence count is the correct denominator for property pricing; the
        # storm sequences hold the authoritative count.
        seq_data = database.get_storm_sequences(catchment)
        if seq_data:
            num_sequences = seq_data.get('num_sequences', len(seq_data.get('sequences', [])))
        else:
            # Fallback: gaugehc num_storms (may overcount if multi-pulse)
            num_sequences = data.get('metadata', {}).get('num_storms', 1000)
            self.log("  Warning: storm sequences not found, using gaugehc num_storms as fallback")

        hazard_curves = data.get('hazard_curves', {})

        # Enrich each gauge with its severe event count from the sequence_gauge
        # records. This gives the true Monte Carlo count rather than the
        # GEV-derived probability in the gauge hazard curves.
        for gid in hazard_curves:
            sg = database.get_sequence_gauge(catchment, gid)
            if sg:
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
