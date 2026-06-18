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

(function(root) {
    'use strict';

    function createNotificationSystem(config) {
        config = config || {};
        var position = config.position || 'top-right';
        var timeout = config.timeout != null ? config.timeout : 5000;
        var maxVisible = config.maxVisible || 5;
        var templates = config.templates || {
            info:    { icon: '\u2139\uFE0F', color: '#2196F3', background: '#E3F2FD' },
            success: { icon: '\u2705',       color: '#4CAF50', background: '#E8F5E8' },
            warning: { icon: '\u26A0\uFE0F', color: '#FF9800', background: '#FFF3E0' },
            error:   { icon: '\u274C',       color: '#f44336', background: '#FFEBEE' },
            loading: { icon: '\uD83D\uDD04', color: '#9E9E9E', background: '#F5F5F5' }
        };

        var queue = [];
        var counter = 0;

        function getContainer() {
            var doc = root.document;
            var c = doc.getElementById('notif-container');
            if (!c) {
                c = doc.createElement('div');
                c.id = 'notif-container';
                c.className = position || 'top-right';
                doc.body.appendChild(c);
            }
            return c;
        }

        function show(message, type, options) {
            type = (type || 'info').toLowerCase();
            options = options || {};
            var tpl = templates[type] || templates.info;
            var id = ++counter;

            queue.push(id);
            while (queue.length > maxVisible) {
                dismiss(queue.shift());
            }

            var doc = root.document;
            var el = doc.createElement('div');
            el.id = 'notif-' + id;
            el.className = 'notif';
            el.style.background = tpl.background;
            el.style.borderLeftColor = tpl.color;

            el.innerHTML =
                '<div class="notif-content">' +
                '<span class="notif-icon">' + tpl.icon + '</span>' +
                '<div class="notif-message">' + message.replace(/\n/g, '<br>') + '</div>' +
                '<button class="notif-close" onclick="window.dismissNotification(' + id + ')">&times;</button>' +
                '</div>';

            el.addEventListener('click', function(e) {
                if (e.target.tagName !== 'BUTTON') dismiss(id);
            });

            getContainer().appendChild(el);
            setTimeout(function() { el.classList.add('show'); }, 10);

            if (!options.persistent && timeout > 0) {
                setTimeout(function() { dismiss(id); }, options.timeout || timeout);
            }

            return id;
        }

        function dismiss(id) {
            var doc = root.document;
            var el = doc.getElementById('notif-' + id);
            if (el) {
                el.classList.remove('show');
                setTimeout(function() { if (el.parentNode) el.parentNode.removeChild(el); }, 300);
            }
            queue = queue.filter(function(n) { return n !== id; });
        }

        function update(id, message, type) {
            var doc = root.document;
            var el = doc.getElementById('notif-' + id);
            if (!el) return;
            var textEl = el.querySelector('div > div');
            if (textEl) textEl.innerHTML = message.replace(/\n/g, '<br>');
            if (type) {
                var tpl = templates[type] || templates.info;
                var iconEl = el.querySelector('span');
                if (iconEl) iconEl.textContent = tpl.icon;
                el.style.background = tpl.background;
                el.style.borderLeftColor = tpl.color;
            }
        }

        function clearAll() {
            queue.forEach(dismiss);
            queue = [];
        }

        function getQueue() { return queue.slice(); }

        return {
            show: show,
            dismiss: dismiss,
            update: update,
            clearAll: clearAll,
            getQueue: getQueue
        };
    }

    // Node.js / Jest export
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { createNotificationSystem: createNotificationSystem };
    }

    // Browser auto-init
    if (typeof root !== 'undefined' && root.document && root.__NOTIF_CONFIG) {
        var api = createNotificationSystem(root.__NOTIF_CONFIG);
        root.showNotification = api.show;
        root.dismissNotification = api.dismiss;
        root.updateNotification = api.update;
        root.clearAllNotifications = api.clearAll;
        root.showSuccess = function(msg, opts) { return api.show(msg, 'success', opts); };
        root.showError = function(msg, opts) { return api.show(msg, 'error', Object.assign({persistent: true}, opts || {})); };
        root.showWarning = function(msg, opts) { return api.show(msg, 'warning', opts); };
        root.showInfo = function(msg, opts) { return api.show(msg, 'info', opts); };
        root.showLoading = function(msg, opts) { return api.show(msg, 'loading', Object.assign({persistent: true}, opts || {})); };
        if (root.console) root.console.log('Notification system initialized');
    }

})(typeof window !== 'undefined' ? window : (typeof global !== 'undefined' ? global : this));
