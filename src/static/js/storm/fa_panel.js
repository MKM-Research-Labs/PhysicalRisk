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

            function createPanel() {
                if (animPanel) return animPanel;

                animPanel = document.createElement('div');
                animPanel.id = 'flood-anim-panel';
                animPanel.style.cssText =
                    'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                    'width:' + PANEL_W + ';height:' + PANEL_H + ';' +
                    'background:var(--panel);border:1px solid var(--divider);border-radius:var(--radius-lg);' +
                    'box-shadow:var(--shadow-toast);z-index:2000;' +
                    'display:none;flex-direction:column;font-family:Arial,sans-serif;';

                // Header
                var header = document.createElement('div');
                header.style.cssText =
                    'display:flex;justify-content:space-between;align-items:center;' +
                    'padding:var(--space-5) var(--space-8);border-bottom:1px solid var(--line-soft);background:var(--wash);' +
                    'border-radius:var(--radius-lg) var(--radius-lg) 0 0;';
                var title = document.createElement('span');
                title.id = 'anim-panel-title';
                title.style.cssText = 'font-weight:bold;font-size:var(--size-14);color:var(--text);';
                title.textContent = 'Flood Animation';
                var closeBtn = document.createElement('button');
                closeBtn.innerHTML = '&times;';
                closeBtn.style.cssText =
                    'border:none;background:none;font-size:var(--size-24);cursor:pointer;color:var(--text-3);padding:0 var(--space-4);line-height:1;';
                closeBtn.onclick = hidePanel;
                header.appendChild(title);
                header.appendChild(closeBtn);

                // Storm selector row
                var selectorRow = document.createElement('div');
                selectorRow.style.cssText = 'padding:var(--space-4) var(--space-8);border-bottom:1px solid var(--line-soft);display:flex;align-items:center;gap:var(--space-6);background:var(--raised);';
                var selLabel = document.createElement('span');
                selLabel.textContent = 'Storm:';
                selLabel.style.cssText = 'font-size:var(--size-sm);font-weight:600;color:var(--text-2);';
                var stormSelect = document.createElement('select');
                stormSelect.id = 'anim-storm-select';
                stormSelect.style.cssText = 'flex:1;padding:var(--space-2) var(--space-4);font-size:var(--size-sm);border:1px solid var(--line-strong);border-radius:var(--radius-4);';
                stormSelect.onchange = function() { loadStorm(this.value); };
                selectorRow.appendChild(selLabel);
                selectorRow.appendChild(stormSelect);

                // Controls row
                var controls = document.createElement('div');
                controls.style.cssText = 'padding:var(--space-4) var(--space-8);border-bottom:1px solid var(--line-soft);display:flex;align-items:center;gap:var(--space-5);';

                var playBtn = document.createElement('button');
                playBtn.id = 'anim-play-btn';
                playBtn.innerHTML = '&#9654;';
                playBtn.style.cssText = 'width:32px;height:32px;border:1px solid var(--line-strong);border-radius:var(--radius-4);background:var(--panel);cursor:pointer;font-size:var(--size-14);';
                playBtn.onclick = togglePlay;

                var speedBtns = document.createElement('div');
                speedBtns.style.cssText = 'display:flex;gap:var(--space-2);';
                [1,2,5].forEach(function(s) {
                    var btn = document.createElement('button');
                    btn.textContent = s + 'x';
                    btn.className = 'anim-speed-btn';
                    btn.dataset.speed = s;
                    btn.style.cssText = 'padding:var(--space-1) var(--space-4);font-size:var(--size-xs);border:1px solid var(--line-strong);border-radius:var(--radius-sm);background:' + (s === 1 ? 'var(--accent-soft)' : 'var(--panel)') + ';cursor:pointer;';
                    btn.onclick = function() { setSpeed(s); };
                    speedBtns.appendChild(btn);
                });

                var scrubber = document.createElement('input');
                scrubber.id = 'anim-scrubber';
                scrubber.type = 'range';
                scrubber.min = '0';
                scrubber.max = '59';
                scrubber.value = '0';
                scrubber.style.cssText = 'flex:1;';
                scrubber.oninput = function() { seekTo(parseInt(this.value)); };

                var hourLabel = document.createElement('span');
                hourLabel.id = 'anim-hour-label';
                hourLabel.style.cssText = 'font-size:var(--size-sm);font-weight:600;min-width:55px;text-align:right;';
                hourLabel.textContent = 'Hour 0';

                controls.appendChild(playBtn);
                controls.appendChild(speedBtns);
                controls.appendChild(scrubber);
                controls.appendChild(hourLabel);

                // Stats bar
                var statsBar = document.createElement('div');
                statsBar.id = 'anim-stats-bar';
                statsBar.style.cssText = 'padding:var(--space-3) var(--space-8);border-bottom:1px solid var(--line-soft);display:flex;gap:var(--space-wide);font-size:var(--size-xs);color:var(--text-3);background:var(--control);';

                // Legend
                var legend = document.createElement('div');
                legend.style.cssText = 'padding:var(--space-2) var(--space-8);border-bottom:1px solid var(--line-soft);display:flex;gap:var(--space-8);font-size:var(--size-xxs);color:var(--text-3);background:var(--panel);align-items:center;';
                legend.innerHTML =
                    '<span style="font-weight:600;">Legend:</span>' +
                    '<span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--accent-bright);margin-right:var(--space-2);vertical-align:middle;"></span>Approaching</span>' +
                    '<span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--amber-bright);margin-right:var(--space-2);vertical-align:middle;"></span>Flooded</span>' +
                    '<span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--red);margin-right:var(--space-2);vertical-align:middle;"></span>Peak/Severe</span>' +
                    '<span style="margin-left:var(--space-6);"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--green-bright);margin-right:var(--space-2);vertical-align:middle;"></span>Gauge Normal</span>' +
                    '<span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--gold-bright);margin-right:var(--space-2);vertical-align:middle;"></span>Alert</span>' +
                    '<span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--amber);margin-right:var(--space-2);vertical-align:middle;"></span>Warning</span>' +
                    '<span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--red);margin-right:var(--space-2);vertical-align:middle;"></span>Severe</span>';

                // Map container
                var mapContainer = document.createElement('div');
                mapContainer.id = 'anim-map-container';
                mapContainer.style.cssText = 'flex:1;position:relative;border-radius:0 0 var(--radius-lg) var(--radius-lg);overflow:hidden;';

                animPanel.appendChild(header);
                animPanel.appendChild(selectorRow);
                animPanel.appendChild(controls);
                animPanel.appendChild(statsBar);
                animPanel.appendChild(legend);
                animPanel.appendChild(mapContainer);
                document.body.appendChild(animPanel);
                return animPanel;
            }
