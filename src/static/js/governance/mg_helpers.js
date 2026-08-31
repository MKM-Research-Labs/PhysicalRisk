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

            var tierColors = Theme.ramp('mission_criticality');
            var tierLabels = {1: 'Tier 1 - Maximum', 2: 'Tier 2 - Substantial', 3: 'Tier 3 - Moderate', 4: 'Tier 4 - Minimal'};
            var reviewColors = Theme.ramp('review_status');
            var catIcons = {'Hazard': '\u26a0\ufe0f', 'Pricing': '\ud83d\udcb0', 'Loss': '\ud83d\udcc9', 'Spatial': '\ud83c\udf0d', 'Valuation': '\ud83c\udfe0', 'Risk': '\ud83d\udcca'};
            var lifecycleColors = Theme.ramp('lifecycle');
            var ragColors = Theme.ramp('rag');

            function badge(text, bg, fg) {
                return '<span style="display:inline-block;padding:var(--space-1) var(--space-4);border-radius:var(--radius-xl);font-size:var(--size-xxs);font-weight:700;background:' + bg + ';color:' + (fg || 'white') + ';">' + text + '</span>';
            }

            function tierBadge(tier) {
                return badge('Tier ' + tier, tierColors[tier] || 'var(--muted-2)');
            }

            function reviewBadge(status) {
                return badge(status, reviewColors[status] || 'var(--muted-2)');
            }

            function statusDot(color) {
                return '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:' + color + ';margin-right:var(--space-2);"></span>';
            }

            function ragBadge(rating) {
                var color = ragColors[rating] || 'var(--grey)';
                return '<span style="display:inline-flex;align-items:center;gap:var(--space-2);"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:' + color + ';border:1px solid ' + color + '88;"></span><span style="font-size:var(--size-xxs);font-weight:600;color:' + color + ';">' + (rating || 'Not Rated') + '</span></span>';
            }

            // ================================================================
            // Editable field definitions (mirrors server-side EDITABLE_FIELDS)
            // ================================================================
            var editableFields = {
                rag_rating: {type: 'choice', options: ['Green', 'Amber', 'Red'], label: 'RAG Rating'},
                owner: {type: 'text', label: 'Model Owner'},
                model_owner_role: {type: 'text', label: 'Owner Role'},
                lifecycle_stage: {type: 'choice', options: ['Development', 'Validation', 'Production', 'Retired'], label: 'Lifecycle Stage'},
                peer_reviewer: {type: 'text', label: 'Peer Reviewer'},
                last_review_date: {type: 'date', label: 'Last Review Date'},
                next_review_date: {type: 'date', label: 'Next Review Date'},
                mrc_signoff_date: {type: 'date', label: 'MRC Signoff Date'},
                recertification_date: {type: 'date', label: 'Recertification Date'},
                validation_status: {type: 'choice', options: ['Initial', 'Pending', 'Validated', 'Conditionally Approved', 'Rejected'], label: 'Validation Status'},
                review_frequency: {type: 'choice', options: ['Monthly', 'Quarterly', 'Semi-annual', 'Annual'], label: 'Review Frequency'},
            };

            function editBtn(field, modelId) {
                return '<button onclick="window.MG.openEdit(\'' + field + '\', \'' + modelId + '\')" style="margin-left:var(--space-3);padding:var(--space-hair) var(--space-3);font-size:var(--size-xxs);border:1px solid var(--divider);border-radius:var(--radius-sm);cursor:pointer;background:var(--control);color:var(--text-3);" title="Edit ' + (editableFields[field] ? editableFields[field].label : field) + '">Edit</button>';
            }

            // ================================================================
            // HTML helpers
            // ================================================================
            function sectionHeader(text) {
                return '<div style="font-size:var(--size-xs);font-weight:700;color:var(--text);text-transform:uppercase;letter-spacing:0.5px;margin-top:var(--space-8);margin-bottom:var(--space-4);padding-bottom:var(--space-2);border-bottom:1px solid var(--line-soft);">' + text + '</div>';
            }

            function infoRow(label, value) {
                return '<div style="display:flex;padding:var(--space-2) 0;font-size:var(--size-xs);">' +
                    '<span style="min-width:130px;color:var(--muted);flex-shrink:0;">' + label + '</span>' +
                    '<span style="color:var(--text);">' + value + '</span></div>';
            }
