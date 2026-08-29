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

(function(root) {
    'use strict';

    function createNotificationSystem(config) {
        config = config || {};
        var position = config.position || 'top-right';
        var timeout = config.timeout != null ? config.timeout : 5000;
        var maxVisible = config.maxVisible || 5;
        var templates = config.templates || {
            info:    { icon: '\u2139\uFE0F', color: Theme.value('accent-bright'), background: Theme.value('accent-soft') },
            success: { icon: '\u2705',       color: Theme.value('green-bright'), background: Theme.value('ok-bg') },
            warning: { icon: '\u26A0\uFE0F', color: Theme.value('amber-bright'), background: Theme.value('warn-bg-warm') },
            error:   { icon: '\u274C',       color: Theme.value('red-bright'), background: Theme.value('danger-bg-soft') },
            loading: { icon: '\uD83D\uDD04', color: Theme.value('grey'), background: Theme.value('sunken') }
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
