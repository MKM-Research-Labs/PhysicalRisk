// Copyright (c) 2022-2026 MKM Research Labs.
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

            function getBaseUrl() {
                var cfg = window.__BACKEND_CONFIG || {};
                return cfg.url || '';
            }

            function fmtGBP(v) {
                if (v == null || v === 0) return '\u2014';
                var cc = (window.__BACKEND_CONFIG || {}).currency || 'GBP';
                var sym = {GBP: '\u00a3', USD: '$', EUR: '\u20ac'}[cc] || (cc + ' ');
                return sym + v.toLocaleString('en-GB', {minimumFractionDigits: 0, maximumFractionDigits: 0});
            }

            function fmtPct(v) {
                if (v == null) return '\u2014';
                return v.toFixed(1) + '%';
            }

            function fmtDepth(v) {
                if (v == null) return '\u2014';
                return v.toFixed(2) + 'm';
            }

            function fmtMonths(v) {
                if (!v) return '\u2014';
                var yrs = Math.floor(v / 12);
                var mos = v % 12;
                return yrs + 'y ' + mos + 'm';
            }

            // Color helpers for sim map
            function spGaugeColor(status) {
                if (status === 'severe') return 'var(--red)';
                if (status === 'warning') return 'var(--amber)';
                if (status === 'alert') return 'var(--gold-bright)';
                return 'var(--green-bright)';
            }
            function spWavefrontColor(p) {
                if (p.peak || (p.flooded && p.depth_m >= 1.0)) return 'var(--red)';
                if (p.flooded) return 'var(--amber-bright)';
                if (p.arrived) return 'var(--accent-bright)';
                return 'var(--accent-pale)';
            }
