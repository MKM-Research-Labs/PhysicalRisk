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

"""Analysis section builders for the portfolio report."""

import statistics as stats_mod

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer

from .styles import ALT_ROWS_AMBER, ALT_ROWS_GREEN  # noqa: F401
from .sections_portfolio import PortfolioSectionsMixin  # noqa: F401


class AnalysisSectionsMixin:
    """Mixin providing analysis section builders for the portfolio report."""

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


# Backward-compatible alias — old name pointed to the single combined mixin.
# Now consumers should inherit from both PortfolioSectionsMixin and AnalysisSectionsMixin.
SectionsMixin = AnalysisSectionsMixin
