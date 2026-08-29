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

            function addMapControl() {
                function findMap() {
                    var mapKey = Object.keys(window).find(function(k) { return k.startsWith('map_'); });
                    if (mapKey) return window[mapKey];
                    return null;
                }

                function tryAdd() {
                    var map = findMap();
                    if (!map) {
                        setTimeout(tryAdd, 500);
                        return;
                    }

                    var GovernanceControl = L.Control.extend({
                        options: { position: 'topright' },
                        onAdd: function() {
                            var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
                            var btn = L.DomUtil.create('a', '', container);
                            btn.href = '#';
                            btn.title = 'Regulatory Compliance';
                            btn.setAttribute('role', 'button');
                            btn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>';
                            btn.style.cssText = 'display:flex;align-items:center;justify-content:center;width:30px;height:30px;cursor:pointer;background:var(--panel);';

                            L.DomEvent.disableClickPropagation(container);
                            L.DomEvent.on(btn, 'click', function(e) {
                                L.DomEvent.preventDefault(e);
                                showMgPanel();
                            });
                            return container;
                        }
                    });

                    new GovernanceControl().addTo(map);
                }

                setTimeout(tryAdd, 1000);
            }

            // Global API
            window.showModelGovernance = showMgPanel;
            window.MG = {
                show: showMgPanel,
                hide: hideMgPanel,
                showDetail: showModelDetail,
                switchDetailTab: switchDetailTab,
                switchDocsSection: switchDocsSection,
                openEdit: openEditModal,
                toggleSort: mgToggleSort,
                setFilter: mgSetFilter,
                setDateFilter: mgSetDateFilter,
                clearFilters: mgClearFilters,
                switchMrcTab: switchMrcSubTab,
                showMeeting: showMrcMeeting,
                switchMeetingTab: switchMeetingTab,
                showNewMeetingForm: showNewMeetingForm,
                createMeeting: createMeeting,
                uploadMeetingDoc: uploadMeetingDoc,
                addNewMeetingDoc: addNewMeetingDoc,
                removeNewMeetingDoc: removeNewMeetingDoc,
                showAgendaForm: showAgendaForm,
                saveAgendaItem: saveAgendaItem,
                deleteAgendaItem: deleteAgendaItem,
                showMinuteForm: showMinuteForm,
                saveMinuteItem: saveMinuteItem,
                deleteMinuteItem: deleteMinuteItem,
                showParticipantForm: showParticipantForm,
                saveParticipant: saveParticipant,
                deleteParticipant: deleteParticipant,
                showDecisionForm: showDecisionForm,
                saveDecision: saveDecision,
                deleteDecision: deleteDecision,
                showActionForm: showActionForm,
                saveAction: saveAction,
                deleteAction: deleteAction,
                downloadMeetingPdf: downloadMeetingPdf,
                toggleBcbs239Principle: toggleBcbs239Principle,
                showBcbs239EditForm: showBcbs239EditForm,
                saveBcbs239Principle: saveBcbs239Principle,
                downloadBcbs239Pdf: downloadBcbs239Pdf,
                toggleVqQuestion: toggleVqQuestion,
                showVqEditForm: showVqEditForm,
                saveVqQuestion: saveVqQuestion,
                showRiskOverrideForm: showRiskOverrideForm,
                saveRiskOverride: saveRiskOverride,
                clearRiskOverride: clearRiskOverride,
                refreshRiskRating: refreshRiskRating,
                showRaciEditRole: showRaciEditRole,
                saveRaciRole: saveRaciRole,
                toggleRaciActivity: toggleRaciActivity,
                showRaciEditActivity: showRaciEditActivity,
                saveRaciActivity: saveRaciActivity,
                showRaciEditEscalation: showRaciEditEscalation,
                saveRaciEscalation: saveRaciEscalation,
                sortBib: window.MG && window.MG.sortBib,
                showBibForm: window.MG && window.MG.showBibForm,
                submitBibRef: window.MG && window.MG.submitBibRef,
                editBibRef: window.MG && window.MG.editBibRef,
                deleteBibRef: window.MG && window.MG.deleteBibRef,
                exportBibtex: window.MG && window.MG.exportBibtex,
                uploadDocument: window.MG && window.MG.uploadDocument,
                downloadDocument: window.MG && window.MG.downloadDocument,
                deleteDocument: window.MG && window.MG.deleteDocument,
            };

            // Add map control button on load
            addMapControl();

            console.log('Model Governance panel ready');
