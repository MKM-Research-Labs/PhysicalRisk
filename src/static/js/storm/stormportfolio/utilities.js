// Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
//
// This software is licensed by MKM Research Labs for non-commercial 
// research and educational use only. Any commercial use, including 
// but not limited to use in or for products or services offered for sale, 
// internal business operations intended for commercial advantage, or
// research and development conducted for a commercial entity, is expressly
// prohibited unless separately authorized in writing by MKM Research Labs.
//
// Use, reproduction, distribution, or modification of this code is subject to the
// terms and conditions of the license agreement provided with this software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

            // ==============================================================
            // Shared utilities
            // ==============================================================
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
                if (status === 'severe') return '#d32f2f';
                if (status === 'warning') return '#f57c00';
                if (status === 'alert') return '#fbc02d';
                return '#4caf50';
            }
            function spWavefrontColor(p) {
                if (p.peak || (p.flooded && p.depth_m >= 1.0)) return '#d32f2f';
                if (p.flooded) return '#ff9800';
                if (p.arrived) return '#2196f3';
                return '#90caf9';
            }
