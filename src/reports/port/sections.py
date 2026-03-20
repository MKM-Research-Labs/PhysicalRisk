# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

"""Section builders for the portfolio report."""

import statistics as stats_mod

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer

from .styles import ALT_ROWS_AMBER, ALT_ROWS_GREEN


class SectionsMixin:
    """Mixin providing section builders for the portfolio report."""

    def _section_gauges(self, data) -> list:
        """Section 1: Gauge Network — table of all gauges."""
        els = [Paragraph('1. Gauge Network', self.section_style)]
        gauges = data['gauges']
        if not gauges:
            els.append(Paragraph('No gauges generated.', self.body_style))
            return els

        header = ['#', 'Gauge ID', 'Lat', 'Lon', 'Alert (m)', 'Warning (m)', 'Severe (m)', 'Tidal']
        rows = []
        for i, g in enumerate(gauges, 1):
            fg = g.get('FloodGauge', g)
            hdr = fg.get('Header', {})
            loc = fg.get('Location', fg.get('SensorDetails', {}).get('GaugeInformation', {}))
            stages = fg.get('FloodStages', fg.get('FloodStage', {}).get('UK', {}))
            tidal = (fg.get('SensorDetails', {})
                     .get('GaugeInformation', {})
                     .get('TidalInfluence', '-'))
            gid = hdr.get('GaugeID', '-')
            lat = loc.get('GaugeLatitude', loc.get('latitude', '-'))
            lon = loc.get('GaugeLongitude', loc.get('longitude', '-'))
            alert = stages.get('FloodAlert', '-')
            warn = stages.get('FloodWarning', '-')
            severe = stages.get('SevereFloodWarning', '-')

            rows.append([
                str(i),
                str(gid)[:18],
                f'{float(lat):.4f}' if lat != '-' else '-',
                f'{float(lon):.4f}' if lon != '-' else '-',
                f'{float(alert):.2f}' if alert != '-' else '-',
                f'{float(warn):.2f}' if warn != '-' else '-',
                f'{float(severe):.2f}' if severe != '-' else '-',
                str(tidal)[:8],
            ])

        cw = [0.3*inch, 1.3*inch, 0.7*inch, 0.7*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.7*inch]
        els.append(self._make_table(header, rows, cw))
        els.append(Spacer(1, 6))
        els.append(Paragraph(f'{len(gauges)} gauges  |  {data["gaugets_count"]} time series  |  '
                             f'{data["gaugehd_count"]} historical daily', self.body_style))
        return els

    def _section_properties(self, data) -> list:
        """Section 2: Properties — table of all properties."""
        els = [Paragraph('2. Properties', self.section_style)]
        props = data['properties']
        if not props:
            els.append(Paragraph('No properties generated.', self.body_style))
            return els

        header = ['#', 'Property ID', 'Lat', 'Lon', 'Type', 'Value', 'Flood Zone']
        rows = []
        for i, p in enumerate(props, 1):
            ph = p.get('PropertyHeader', p.get('Property', p))
            hdr = ph.get('Header', {})
            loc = ph.get('Location', {})
            attrs = ph.get('PropertyAttributes', ph.get('PropertyCharacteristics', {}))
            val_block = ph.get('Valuation', {})
            risk = ph.get('RiskAssessment', ph.get('FloodRisk', {}))

            pid = hdr.get('PropertyID', '-')
            lat = loc.get('LatitudeDegrees', loc.get('PropertyLatitude', '-'))
            lon = loc.get('LongitudeDegrees', loc.get('PropertyLongitude', '-'))
            ptype = attrs.get('PropertyResi', attrs.get('propertyType',
                     attrs.get('PropertyType', hdr.get('propertyType', '-'))))
            val = val_block.get('PropertyValue', val_block.get('MarketValue', '-'))
            fz = risk.get('EAFloodZone', risk.get('FloodZone', '-'))
            val_str = f'{float(val):,.0f}' if val != '-' and val is not None else '-'

            rows.append([
                str(i), str(pid)[:16],
                f'{float(lat):.4f}' if lat != '-' else '-',
                f'{float(lon):.4f}' if lon != '-' else '-',
                str(ptype)[:12], val_str, str(fz),
            ])

        cw = [0.3*inch, 1.2*inch, 0.7*inch, 0.7*inch, 0.9*inch, 0.9*inch, 0.8*inch]
        els.append(self._make_table(header, rows, cw, ALT_ROWS_GREEN))
        els.append(Spacer(1, 6))
        els.append(Paragraph(f'{len(props)} properties  |  {data["propertyts_count"]} flood time series',
                             self.body_style))
        return els

    def _section_mortgages(self, data) -> list:
        """Section 3: Mortgages."""
        els = [Paragraph('3. Mortgages', self.section_style)]
        mortgages = data['mortgages']
        if not mortgages:
            els.append(Paragraph('No mortgages generated.', self.body_style))
            return els

        header = ['#', 'Mortgage ID', 'Property ID', 'LTV (%)', 'Term (mo)', 'Rate (%)', 'Balance']
        rows = []
        for i, m in enumerate(mortgages, 1):
            mg = m.get('Mortgage', m)
            hdr = mg.get('Header', {})
            ft = mg.get('FinancialTerms', mg.get('Terms', {}))
            cs = mg.get('CurrentStatus', {})

            mid = hdr.get('MortgageID', mg.get('mortgage_id', '-'))
            pid = hdr.get('PropertyID', mg.get('property_id', '-'))
            ltv = ft.get('OriginalLTV', ft.get('LTV', '-'))
            term = ft.get('OriginalTerm', ft.get('TermYears', '-'))
            rate = ft.get('OriginalLendingRate', ft.get('InterestRate', '-'))
            bal = cs.get('OutstandingBalance',
                         ft.get('OutstandingBalance', '-'))

            ltv_str = f'{float(ltv):.1f}' if ltv != '-' and ltv is not None else '-'
            rate_str = f'{float(rate):.2f}' if rate != '-' and rate is not None else '-'
            bal_str = f'{float(bal):,.0f}' if bal != '-' and bal is not None else '-'

            rows.append([
                str(i), str(mid)[:16], str(pid)[:16],
                ltv_str, str(term), rate_str, bal_str,
            ])

        cw = [0.3*inch, 1.1*inch, 1.1*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.9*inch]
        els.append(self._make_table(header, rows, cw, ALT_ROWS_AMBER))
        els.append(Spacer(1, 6))
        els.append(Paragraph(f'{len(mortgages)} mortgages linked', self.body_style))
        return els

    def _section_gaugehd(self, data) -> list:
        """Section 4: Historical Gauges — baselines table."""
        els = [Paragraph('4. Historical Gauge Data', self.section_style)]
        baselines = data['gaugehd_baselines']
        if not baselines:
            els.append(Paragraph(f'{data["gaugehd_count"]} gaugehd files (no baseline detail available).',
                                 self.body_style))
            return els

        header = ['#', 'Gauge ID', 'Mean Level (m)', 'Winter DJF (m)', 'Summer JJA (m)', 'Range (m)']
        rows = []
        for i, bl in enumerate(baselines, 1):
            w = bl.get('winter')
            s = bl.get('summer')
            rng = f'{w - s:.3f}' if w is not None and s is not None else '-'
            rows.append([
                str(i), str(bl['gauge_id'])[:18],
                f'{bl["mean_level"]:.3f}',
                f'{w:.3f}' if w is not None else '-',
                f'{s:.3f}' if s is not None else '-',
                rng,
            ])

        cw = [0.3*inch, 1.3*inch, 1.1*inch, 1.1*inch, 1.1*inch, 0.8*inch]
        els.append(self._make_table(header, rows, cw))
        els.append(Spacer(1, 6))

        if any(bl.get('winter') for bl in baselines):
            winters = [bl['winter'] for bl in baselines if bl.get('winter')]
            summers = [bl['summer'] for bl in baselines if bl.get('summer')]
            avg_w = stats_mod.mean(winters)
            avg_s = stats_mod.mean(summers)
            els.append(Paragraph(
                f'Avg winter baseline (DJF): {avg_w:.3f} m  |  '
                f'Avg summer baseline (JJA): {avg_s:.3f} m  |  '
                f'Seasonal range: {avg_w - avg_s:.3f} m', self.body_style))
        return els

    def _section_storms(self, data) -> list:
        """Section 5: Storm Sequences."""
        els = [Paragraph('5. Storm Sequences', self.section_style)]
        ss = data['seq_summary']
        seq_count = ss.get('num_sequences', 0)

        pairs = [('Sequences generated', f'{seq_count:,}')]
        tc = ss.get('sequence_type_counts', {})
        if tc:
            pairs.append(('Sequence types', ', '.join(f'{k}: {v:,}' for k, v in sorted(tc.items()))))
        ic = ss.get('intensity_category_counts', {})
        if ic:
            pairs.append(('Intensity categories', ', '.join(f'{k}: {v:,}' for k, v in sorted(ic.items()))))
        precip = ss.get('precipitation_mm', {})
        if precip:
            pairs.append(('Precipitation (mm)',
                          f'min {precip["min"]:.0f} / mean {precip["mean"]:.0f} / max {precip["max"]:.0f}'))
        dur = ss.get('duration_hours', {})
        if dur:
            pairs.append(('Duration (hours)',
                          f'min {dur["min"]:.0f} / mean {dur["mean"]:.0f} / max {dur["max"]:.0f}'))

        # Stress testing
        stress_count = len(data['stress_storms'].get('storms', []))
        pairs.append(('Alert-breaching storms', f'{stress_count:,}'))
        pairs.append(('GBM classifiers trained', str(data['classifier_count'])))
        ts = data['training_summary']
        if ts.get('avg_auc_roc'):
            pairs.append(('Average AUC-ROC', f'{ts["avg_auc_roc"]:.4f}'))

        els.append(self._kv_table(pairs))
        return els

    def _section_hazard_curves(self, data) -> list:
        """Section 6: Hazard Curves — per-gauge exceedance points."""
        els = [Paragraph('6. Hazard Curves', self.section_style)]
        hc = data['gaugehc'].get('hazard_curves', {})
        if not hc:
            els.append(Paragraph('No hazard curves available.', self.body_style))
            return els

        els.append(Paragraph(f'{len(hc)} gauge hazard curves (GEV fit)', self.body_style))
        els.append(Spacer(1, 4))

        header = ['Gauge ID', 'P(Alert)', 'P(Warning)', 'P(Severe)',
                  'RL 10yr (m)', 'RL 50yr (m)', 'RL 100yr (m)']
        rows = []

        def _fmt_p(v):
            if v == '-' or v is None:
                return '-'
            return f'{float(v)*100:.2f}%'

        def _fmt_rl(v):
            if v == '-' or v is None:
                return '-'
            return f'{float(v):.2f}'

        for gid in sorted(hc):
            gc = hc[gid]
            if isinstance(gc, dict):
                p_a = gc.get('annual_flood_prob_alert',
                             gc.get('exceedance_probabilities', {}).get('alert', '-'))
                p_w = gc.get('annual_flood_prob_warning',
                             gc.get('exceedance_probabilities', {}).get('warning', '-'))
                p_s = gc.get('annual_flood_prob_severe',
                             gc.get('exceedance_probabilities', {}).get('severe', '-'))
                rpl = gc.get('return_period_levels', gc.get('return_levels', {}))
                rl10 = rpl.get('10yr', rpl.get('10', rpl.get(10, '-')))
                rl50 = rpl.get('50yr', rpl.get('50', rpl.get(50, '-')))
                rl100 = rpl.get('100yr', rpl.get('100', rpl.get(100, '-')))
            else:
                p_a = p_w = p_s = rl10 = rl50 = rl100 = '-'

            rows.append([
                str(gid)[:18], _fmt_p(p_a), _fmt_p(p_w), _fmt_p(p_s),
                _fmt_rl(rl10), _fmt_rl(rl50), _fmt_rl(rl100),
            ])

        cw = [1.3*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch]
        els.append(self._make_table(header, rows, cw))

        phc_count = len(data['propertyhc'].get('property_hazard_curves', {}))
        if phc_count:
            els.append(Spacer(1, 6))
            els.append(Paragraph(f'{phc_count} property hazard curves generated', self.body_style))
        return els

    def _section_propertyts(self, data) -> list:
        """Section 7/8: Property Flood Time Series + Property Hazard Curves."""
        els = [Paragraph('7. Property Flood Time Series', self.section_style)]
        pts = data['propertyts_count']
        phc = len(data['propertyhc'].get('property_hazard_curves', {}))
        els.append(Paragraph(f'{pts} property flood time series files generated', self.body_style))
        if phc:
            els.append(Spacer(1, 8))
            els.append(Paragraph('8. Property Hazard Curves + PRS Pricing', self.section_style))
            els.append(Paragraph(f'{phc} property hazard curves with PRS pricing', self.body_style))
        return els

    def _section_counterparties(self, data) -> list:
        """Section 9: Counterparties."""
        els = [Paragraph('9. Counterparties', self.section_style)]
        ctps = data['counterparties']
        if not ctps:
            els.append(Paragraph('No counterparties generated.', self.body_style))
            return els

        header = ['#', 'Counterparty ID', 'Name', 'Type', 'Rating', 'Jurisdiction']
        rows = []
        for i, c in enumerate(ctps, 1):
            cs = c.get('CounterpartySet', c.get('Counterparty', c))
            party = cs.get('Party', {})
            plat = cs.get('_platform', {})

            cid = (party.get('PartyID')
                   or cs.get('Header', {}).get('CounterpartyID')
                   or '-')
            name = (plat.get('ShortName')
                    or party.get('PartyName')
                    or cs.get('Details', {}).get('Name')
                    or '-')
            ctype = (plat.get('PartyType')
                     or cs.get('Details', {}).get('Type')
                     or '-')
            rating = (plat.get('CreditRating')
                      or cs.get('CreditProfile', {}).get('Rating')
                      or '-')
            jurisdiction = (plat.get('Jurisdiction')
                            or cs.get('Details', {}).get('Sector')
                            or '-')
            rows.append([
                str(i), str(cid)[:16], str(name)[:20],
                str(ctype)[:12], str(rating), str(jurisdiction)[:14],
            ])

        cw = [0.3*inch, 1.2*inch, 1.5*inch, 0.9*inch, 0.6*inch, 1.0*inch]
        els.append(self._make_table(header, rows, cw, ALT_ROWS_GREEN))
        return els

    def _section_blotter(self, data) -> list:
        """Section 10: Trading Book."""
        els = [Paragraph('10. Trading Book', self.section_style)]
        pairs = [
            ('PRS trades', str(data['trade_count'])),
            ('Historical EOD snapshots', str(data['eod_count'])),
        ]
        els.append(self._kv_table(pairs))
        return els

    def _section_summary(self, data) -> list:
        """Summary section — aggregate statistics."""
        els = [Paragraph('Summary', self.section_style)]

        gauges = data['gauges']
        props = data['properties']
        morts = data['mortgages']
        ctps = data['counterparties']
        seq_count = data['seq_summary'].get('num_sequences', 0)
        stress_count = len(data['stress_storms'].get('storms', []))
        hc_count = len(data['gaugehc'].get('hazard_curves', {}))
        phc_count = len(data['propertyhc'].get('property_hazard_curves', {}))

        pairs = [
            ('Gauges', str(len(gauges))),
            ('Gauge time series (gaugets)', str(data['gaugets_count'])),
            ('Gauge historical daily (gaugehd)', str(data['gaugehd_count'])),
            ('Properties', str(len(props))),
            ('Property flood time series', str(data['propertyts_count'])),
            ('Mortgages', str(len(morts))),
            ('Counterparties', str(len(ctps))),
            ('Storm sequences', f'{seq_count:,}'),
            ('Alert-breaching storms', f'{stress_count:,}'),
            ('Gauge hazard curves', str(hc_count)),
            ('Property hazard curves', str(phc_count)),
            ('GBM classifiers', str(data['classifier_count'])),
            ('PRS trades', str(data['trade_count'])),
            ('EOD snapshots', str(data['eod_count'])),
        ]

        # Data size
        try:
            total_bytes = sum(
                f.stat().st_size for f in self.input_dir.rglob('*') if f.is_file()
            )
            if total_bytes > 1_073_741_824:
                size_str = f'{total_bytes / 1_073_741_824:.2f} GB'
            else:
                size_str = f'{total_bytes / 1_048_576:.1f} MB'
            pairs.append(('Total data size', size_str))
        except Exception:
            pass

        els.append(self._kv_table(pairs))
        return els
