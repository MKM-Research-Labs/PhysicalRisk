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
            var _cfg = window.__PROPDETAILS_CONFIG || {};
            var PANEL_W = _cfg.panelWidth || '620px';
            var PANEL_H = _cfg.panelHeight || '560px';
            var propPanel = null;

            function createPanel() {
                if (propPanel) return propPanel;

                propPanel = document.createElement('div');
                propPanel.id = 'property-details-panel';
                propPanel.style.cssText =
                    'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                    'width:' + PANEL_W + ';height:' + PANEL_H + ';' +
                    'background:white;border:1px solid #ccc;border-radius:8px;' +
                    'box-shadow:0 4px 20px rgba(0,0,0,0.3);z-index:2000;' +
                    'display:none;flex-direction:column;font-family:Arial,sans-serif;';

                var header = document.createElement('div');
                header.style.cssText =
                    'display:flex;justify-content:space-between;align-items:center;' +
                    'padding:10px 16px;border-bottom:1px solid #eee;background:#f8f9fa;' +
                    'border-radius:8px 8px 0 0;';

                var title = document.createElement('span');
                title.id = 'property-details-title';
                title.style.cssText = 'font-weight:bold;font-size:14px;color:#1a5276;';

                var closeBtn = document.createElement('button');
                closeBtn.innerHTML = '&times;';
                closeBtn.style.cssText =
                    'border:none;background:none;font-size:24px;cursor:pointer;' +
                    'color:#666;padding:0 8px;line-height:1;';
                closeBtn.onclick = hidePanel;

                header.appendChild(title);
                header.appendChild(closeBtn);

                var content = document.createElement('div');
                content.id = 'property-details-content';
                content.style.cssText = 'flex:1;padding:12px 16px;overflow-y:auto;font-size:13px;';

                propPanel.appendChild(header);
                propPanel.appendChild(content);
                document.body.appendChild(propPanel);

                document.addEventListener('keydown', function(e) {
                    if (e.key === 'Escape' && propPanel.style.display !== 'none') hidePanel();
                });

                return propPanel;
            }

            function hidePanel() {
                if (propPanel) propPanel.style.display = 'none';
            }

            function fmt(v) {
                if (v === null || v === undefined) return 'N/A';
                return String(v);
            }

            function fmtCurrency(v) {
                if (typeof v !== 'number') return fmt(v);
                return '£' + v.toLocaleString('en-GB', {maximumFractionDigits: 0});
            }

            function fmtBool(v) {
                if (v === true) return 'Yes';
                if (v === false) return 'No';
                return fmt(v);
            }

            function section(title, color, rows) {
                var html = '<div style="margin-bottom:14px;">' +
                    '<div style="font-weight:700;font-size:12px;color:' + color + ';' +
                    'border-bottom:1px solid #eee;padding-bottom:4px;margin-bottom:6px;">' +
                    title + '</div>';
                rows.forEach(function(r) {
                    if (r[1] === 'N/A') return;
                    html += '<div style="display:flex;justify-content:space-between;padding:2px 0;">' +
                        '<span style="color:#666;">' + r[0] + '</span>' +
                        '<span style="font-weight:600;color:#333;">' + r[1] + '</span></div>';
                });
                html += '</div>';
                return html;
            }

            async function showPanel(propertyId) {
                var panel = createPanel();
                var title = document.getElementById('property-details-title');
                var content = document.getElementById('property-details-content');

                var label = window.propertyDisplayName ? window.propertyDisplayName(propertyId) : propertyId;
                title.textContent = label;
                content.innerHTML = '<p style="color:#999;text-align:center;padding-top:20px;">Loading...</p>';
                panel.style.display = 'flex';

                try {
                    var cfg = window.__BACKEND_CONFIG || {};
                    var baseUrl = cfg.url || '';
                    var response = await fetch(baseUrl + '/api/v1/properties/' + propertyId, {mode: 'cors'});
                    if (!response.ok) throw new Error('HTTP ' + response.status);
                    var data = await response.json();
                    if (data.status !== 'success') throw new Error(data.message || 'No data');

                    var ph  = (data.property || {}).PropertyHeader || {};
                    var hdr = ph.Header || {};
                    var loc = ph.Location || {};
                    var con = ph.Construction || {};
                    var val = ph.Valuation || {};
                    var att = ph.PropertyAttributes || {};
                    var risk = ph.RiskAssessment || {};
                    var gauges = ph.ReferenceGauges || [];

                    var html = '';

                    html += section('Property', '#1a5276', [
                        ['Property ID',  fmt(hdr.PropertyID)],
                        ['UPRN',         fmt(hdr.UPRN)],
                        ['Type',         fmt(hdr.propertyType)],
                        ['Status',       fmt(hdr.propertyStatus)],
                        ['Catchment',    fmt(hdr.CatchmentID)],
                    ]);

                    html += section('Address', '#154360', [
                        ['Building',     fmt(loc.BuildingNumber) + (loc.SubBuildingNumber ? ' (' + loc.SubBuildingNumber + ')' : '')],
                        ['Street',       fmt(loc.StreetName)],
                        ['Town / City',  fmt(loc.TownCity)],
                        ['County',       fmt(loc.County)],
                        ['Postcode',     fmt(loc.Postcode)],
                        ['Local Auth.',  fmt(loc.LocalAuthority)],
                        ['Coordinates',  loc.LatitudeDegrees ? loc.LatitudeDegrees.toFixed(5) + 'N, ' + loc.LongitudeDegrees.toFixed(5) + 'E' : 'N/A'],
                    ]);

                    html += section('Property Attributes', '#1b5e20', [
                        ['Occupancy',    fmt(att.OccupancyType)],
                        ['Area',         att.PropertyAreaSqm ? att.PropertyAreaSqm.toFixed(0) + ' m²' : 'N/A'],
                        ['Storeys',      fmt(att.NumberOfStoreys)],
                        ['Bedrooms',     fmt(att.NumberBedrooms)],
                        ['Bathrooms',    fmt(att.NumberBathrooms)],
                        ['Built',        fmt(att.ConstructionYear)],
                        ['Period',       fmt(att.PropertyPeriod)],
                        ['Condition',    fmt(att.PropertyCondition)],
                        ['Council Tax',  fmt(att.CouncilTaxBand)],
                    ]);

                    html += section('Construction', '#4a235a', [
                        ['Type',         fmt(con.ConstructionType)],
                        ['Foundation',   fmt(con.FoundationType)],
                        ['Floor Type',   fmt(con.FloorType)],
                        ['Floor Level',  con.FloorLevelMeters != null ? con.FloorLevelMeters.toFixed(2) + ' m' : 'N/A'],
                        ['Basement',     fmtBool(con.BasementPresent)],
                    ]);

                    html += section('Valuation', '#7d6608', [
                        ['Property Value', fmtCurrency(val.PropertyValue)],
                        ['Valuation Date', fmt(val.ValuationDate)],
                        ['Method',         fmt(val.ValuationMethod)],
                    ]);

                    html += section('Flood Risk', '#922b21', [
                        ['EA Flood Zone',   fmt(risk.EAFloodZone)],
                        ['Overall Risk',    fmt(risk.OverallFloodRisk)],
                        ['Risk Type',       fmt(risk.FloodRiskType)],
                        ['Ground Level',    risk.GroundLevelMeters != null ? risk.GroundLevelMeters.toFixed(2) + ' m AOD' : 'N/A'],
                        ['River Distance',  risk.RiverDistanceMeters != null ? risk.RiverDistanceMeters.toFixed(0) + ' m' : 'N/A'],
                        ['Coastal Dist.',   risk.CoastalDistanceMeters != null ? (risk.CoastalDistanceMeters/1000).toFixed(1) + ' km' : 'N/A'],
                        ['Soil Type',       fmt(risk.SoilType)],
                        ['Govt. Defence',   fmtBool(risk.GovernmentalDefenceScheme)],
                        ['Nearest Gauges',  gauges.length ? gauges.slice(0,3).join(', ') : 'N/A'],
                    ]);

                    content.innerHTML = html;
                } catch (error) {
                    content.innerHTML = '<p style="color:#d32f2f;text-align:center;">Error: ' + error.message + '</p>';
                }
            }

            window.PropertyDetailsPanel = {
                show: showPanel,
                hide: hidePanel
            };
        })();
        
