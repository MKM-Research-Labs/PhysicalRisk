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

(function() {
    var _navCfg = window.__NAV_MENU_CONFIG || {};
    var gaugeMenuItems = _navCfg.gauge || [];
    var propertyMenuItems = _navCfg.property || [];

    var container = document.createElement('div');
    container.id = 'nav-menu-container';

    // Gauge select
    var gSel = document.createElement('select');
    gSel.id = 'nav-gauge-select';
    gSel.innerHTML = '<option value="">Gauges</option>';

    // Property select
    var pSel = document.createElement('select');
    pSel.id = 'nav-prop-select';
    pSel.innerHTML = '<option value="">Properties</option>';

    // Action bar (hidden until selection)
    var actionBar = document.createElement('div');
    actionBar.id = 'nav-action-bar';

    container.appendChild(gSel);
    container.appendChild(pSel);
    container.appendChild(actionBar);
    document.body.appendChild(container);

    function showActions(entityId, entityLabel, menuItems) {
        actionBar.innerHTML = '';
        if (!entityId) return;
        menuItems.forEach(function(mi) {
            var btn = document.createElement('button');
            btn.textContent = mi.label;
            btn.onclick = function() {
                if (window[mi.action]) window[mi.action](entityId, entityLabel);
            };
            actionBar.appendChild(btn);
        });
    }

    gSel.onchange = function() {
        pSel.value = '';
        var gid = gSel.value;
        var label = gSel.options[gSel.selectedIndex].text;
        showActions(gid, label, gaugeMenuItems);
    };

    pSel.onchange = function() {
        gSel.value = '';
        var pid = pSel.value;
        showActions(pid, pid, propertyMenuItems);
    };

    // Populate when preloader data arrives
    function populateGauges() {
        if (!window._tdPreGauges || !window._tdPreGauges.gauges) return false;
        var gauges = window._tdPreGauges.gauges
            .filter(function(g) { return g.gaugeId && g.gaugeId.indexOf('SYNTH') !== 0; })
            .sort(function(a, b) { return (a.name || a.gaugeId).localeCompare(b.name || b.gaugeId); });
        gSel.innerHTML = '<option value="">Gauges (' + gauges.length + ')</option>';
        gauges.forEach(function(g) {
            var opt = document.createElement('option');
            opt.value = g.gaugeId;
            opt.textContent = g.name || g.gaugeId;
            gSel.appendChild(opt);
        });
        return true;
    }

    function populateProperties() {
        if (!window._prePropertyTS || !window._prePropertyTS.data || !window._prePropertyTS.data.properties) return false;
        var props = window._prePropertyTS.data.properties
            .sort(function(a, b) { return (a.property_id || '').localeCompare(b.property_id || ''); });
        pSel.innerHTML = '<option value="">Properties (' + props.length + ')</option>';
        props.forEach(function(p) {
            var opt = document.createElement('option');
            opt.value = p.property_id;
            opt.textContent = window.propertyDisplayName(p.property_id);
            pSel.appendChild(opt);
        });
        return true;
    }

    var tries = 0;
    var poll = setInterval(function() {
        tries++;
        var gDone = populateGauges();
        var pDone = populateProperties();
        if ((gDone && pDone) || tries > 120) clearInterval(poll);
    }, 500);
})();
