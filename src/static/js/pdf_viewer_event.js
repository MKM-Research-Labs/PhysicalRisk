
            document.addEventListener('__EVENT_NAME__', function(e) {
                if (e.detail && e.detail.__EVENT_ID_KEY__ && e.detail.pdfBase64) {
                    showPanel(e.detail.__EVENT_ID_KEY__, e.detail.pdfBase64);
                }
            });