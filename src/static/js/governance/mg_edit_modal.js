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

            function openEditModal(field, modelId) {
                var spec = editableFields[field];
                if (!spec) return;

                var m = window._mgCurrentModel;
                var currentVal = m ? (m[field] || '') : '';

                // Remove existing modal
                var old = document.getElementById('mg-edit-modal');
                if (old) old.remove();

                var overlay = document.createElement('div');
                overlay.id = 'mg-edit-modal';
                overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:var(--scrim);z-index:3000;display:flex;align-items:center;justify-content:center;';

                var dialog = document.createElement('div');
                dialog.style.cssText = 'background:var(--panel);border-radius:var(--radius-lg);box-shadow:var(--shadow-modal);width:420px;max-width:90vw;font-family:Arial,sans-serif;';

                // Header
                var hdr = document.createElement('div');
                hdr.style.cssText = 'padding:var(--space-8) var(--space-wide);border-bottom:1px solid var(--line-soft);';
                hdr.innerHTML = '<div style="font-size:var(--size-14);font-weight:700;color:var(--text);">Edit ' + spec.label + '</div><div style="font-size:var(--size-xs);color:var(--muted);margin-top:var(--space-1);">Model: ' + modelId + '</div>';

                // Body
                var body = document.createElement('div');
                body.style.cssText = 'padding:var(--space-8) var(--space-wide);';

                // Current value
                body.innerHTML = '<div style="font-size:var(--size-xs);color:var(--text-3);margin-bottom:var(--space-6);">Current value: <b>' + (currentVal || '\u2014') + '</b></div>';

                // Input
                var inputHtml = '';
                if (spec.type === 'choice') {
                    inputHtml = '<select id="mg-edit-value" style="width:100%;padding:var(--space-4);font-size:var(--size-sm);border:1px solid var(--line-strong);border-radius:var(--radius-4);">';
                    spec.options.forEach(function(opt) {
                        inputHtml += '<option value="' + opt + '"' + (opt === currentVal ? ' selected' : '') + '>' + opt + '</option>';
                    });
                    inputHtml += '</select>';
                } else if (spec.type === 'date') {
                    inputHtml = '<input type="date" id="mg-edit-value" value="' + currentVal + '" style="width:100%;padding:var(--space-4);font-size:var(--size-sm);border:1px solid var(--line-strong);border-radius:var(--radius-4);box-sizing:border-box;">';
                } else {
                    inputHtml = '<input type="text" id="mg-edit-value" value="' + currentVal + '" style="width:100%;padding:var(--space-4);font-size:var(--size-sm);border:1px solid var(--line-strong);border-radius:var(--radius-4);box-sizing:border-box;">';
                }
                body.innerHTML += '<label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-2);">New Value</label>' + inputHtml;

                // Reason
                body.innerHTML += '<div style="margin-top:var(--space-6);"><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-2);">Reason for Change (required)</label><textarea id="mg-edit-reason" rows="3" style="width:100%;padding:var(--space-4);font-size:var(--size-sm);border:1px solid var(--line-strong);border-radius:var(--radius-4);resize:vertical;box-sizing:border-box;" placeholder="Explain why this change is being made..."></textarea></div>';

                // Error
                body.innerHTML += '<div id="mg-edit-error" style="display:none;margin-top:var(--space-4);padding:var(--space-3) var(--space-5);background:var(--danger-bg-soft);color:var(--red-dark);border-radius:var(--radius-4);font-size:var(--size-xs);"></div>';

                // Footer
                var footer = document.createElement('div');
                footer.style.cssText = 'padding:var(--space-6) var(--space-wide);border-top:1px solid var(--line-soft);display:flex;gap:var(--space-4);justify-content:flex-end;';

                var cancelBtn = document.createElement('button');
                cancelBtn.textContent = 'Cancel';
                cancelBtn.style.cssText = 'padding:var(--space-4) var(--space-9);font-size:var(--size-sm);border:1px solid var(--line-strong);border-radius:var(--radius-4);cursor:pointer;background:var(--panel);color:var(--text-3);';
                cancelBtn.onclick = function() { overlay.remove(); };

                var confirmBtn = document.createElement('button');
                confirmBtn.textContent = 'Confirm Change';
                confirmBtn.style.cssText = 'padding:var(--space-4) var(--space-9);font-size:var(--size-sm);border:none;border-radius:var(--radius-4);cursor:pointer;background:var(--accent);color:var(--inverse);font-weight:600;';
                confirmBtn.onclick = function() {
                    var newVal = document.getElementById('mg-edit-value').value.trim();
                    var reason = document.getElementById('mg-edit-reason').value.trim();
                    var err = document.getElementById('mg-edit-error');

                    if (!newVal) {
                        err.textContent = 'Please select or enter a new value.';
                        err.style.display = 'block';
                        return;
                    }
                    if (!reason) {
                        err.textContent = 'A reason is required for all governance changes.';
                        err.style.display = 'block';
                        return;
                    }
                    if (newVal === currentVal) {
                        err.textContent = 'New value is the same as the current value.';
                        err.style.display = 'block';
                        return;
                    }

                    confirmBtn.disabled = true;
                    confirmBtn.textContent = 'Saving...';

                    fetch(getBaseUrl() + '/api/v1/governance/models/' + modelId + '/update', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            field: field,
                            value: newVal,
                            reason: reason,
                            user: 'David K Kelly',
                        }),
                    })
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status === 'success') {
                            overlay.remove();
                            // Refresh the model detail view
                            showModelDetail(modelId);
                        } else {
                            err.textContent = data.message || 'Update failed';
                            err.style.display = 'block';
                            confirmBtn.disabled = false;
                            confirmBtn.textContent = 'Confirm Change';
                        }
                    })
                    .catch(function(e) {
                        err.textContent = 'Network error: ' + e.message;
                        err.style.display = 'block';
                        confirmBtn.disabled = false;
                        confirmBtn.textContent = 'Confirm Change';
                    });
                };

                footer.appendChild(cancelBtn);
                footer.appendChild(confirmBtn);

                dialog.appendChild(hdr);
                dialog.appendChild(body);
                dialog.appendChild(footer);
                overlay.appendChild(dialog);

                // Close on overlay click
                overlay.addEventListener('click', function(e) {
                    if (e.target === overlay) overlay.remove();
                });

                document.body.appendChild(overlay);
            }
