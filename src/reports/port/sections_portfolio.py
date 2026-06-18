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

"""Portfolio entity-level section builders for the portfolio report."""

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer

from .styles import ALT_ROWS_AMBER, ALT_ROWS_GREEN


class PortfolioSectionsMixin:
    """Mixin providing portfolio entity-level section builders."""

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
            mg = m.get('RLoan', m)
            hdr = mg.get('Header', {})
            ft = mg.get('FinancialTerms', mg.get('Terms', {}))
            cs = mg.get('CurrentStatus', {})

            mid = hdr.get('RLoanID', mg.get('mortgage_id', '-'))
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
