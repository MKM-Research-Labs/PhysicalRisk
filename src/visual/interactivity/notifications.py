# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
User notification system for interactive map functionality.

Provides toast-style notifications for user feedback in the map interface.
"""

import json
from enum import Enum
from typing import Any, Dict

import folium

from visual.interactivity._jsbundle import js_static
from config.theme import colour


class NotificationType(Enum):
    """Notification types with associated styling."""
    INFO = ("info", "ℹ️", colour('accent-bright'), colour('accent-soft'))
    SUCCESS = ("success", "✅", colour('green-bright'), colour('flood-none'))
    WARNING = ("warning", "⚠️", colour('amber-bright'), colour('warn-bg-warm'))
    ERROR = ("error", "❌", colour('red-bright'), colour('danger-bg-soft'))
    LOADING = ("loading", "🔄", colour('grey'), colour('sunken'))

    def __init__(self, key: str, icon: str, color: str, background: str):
        self.key = key
        self.icon = icon
        self.color = color
        self.background = background


class NotificationPosition(Enum):
    """Notification container positions."""
    TOP_RIGHT = "top-right"
    TOP_LEFT = "top-left"
    TOP_CENTER = "top-center"
    BOTTOM_RIGHT = "bottom-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_CENTER = "bottom-center"


class NotificationSystem:
    """Toast notification system for map interactions."""

    def __init__(self,
                 position: NotificationPosition = NotificationPosition.TOP_RIGHT,
                 timeout: int = 5000,
                 max_visible: int = 5):
        """
        Initialize notification system.

        Args:
            position: Screen position for notifications
            timeout: Auto-dismiss timeout in milliseconds
            max_visible: Maximum simultaneous notifications
        """
        self.position = position
        self.timeout = timeout
        self.max_visible = max_visible

    def _build_templates_js(self) -> str:
        """Build JS object for notification templates."""
        templates = {
            t.key: {"icon": t.icon, "color": t.color, "background": t.background}
            for t in NotificationType
        }
        return json.dumps(templates)

    def _build_position_css(self) -> str:
        """Build CSS for position mapping."""
        return js_static('notifications_position.js')

    def get_js(self) -> str:
        """Generate the notification system CSS and JavaScript."""
        from config import config
        static_dir = config.get_static_dir()
        css_code = (static_dir / 'css' / 'notifications.css').read_text()
        js_code = (static_dir / 'js' / 'notifications.js').read_text()
        notif_config = json.dumps({
            'position': self.position.value,
            'timeout': self.timeout,
            'maxVisible': self.max_visible,
            'templates': {
                t.key: {"icon": t.icon, "color": t.color, "background": t.background}
                for t in NotificationType
            }
        })
        return f"<style>{css_code}</style>\n<script>window.__NOTIF_CONFIG = {notif_config};\n{js_code}</script>"

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add notification system to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def configure(self, position: NotificationPosition = None,
                 timeout: int = None, max_visible: int = None) -> None:
        """Update configuration."""
        if position:
            self.position = position
        if timeout is not None:
            self.timeout = timeout
        if max_visible is not None:
            self.max_visible = max_visible

    def get_statistics(self) -> Dict[str, Any]:
        """Get configuration statistics."""
        return {
            'default_position': self.position.value,
            'auto_dismiss_timeout': self.timeout,
            'max_notifications': self.max_visible,
            'available_types': [t.key for t in NotificationType],
            'available_positions': [p.value for p in NotificationPosition]
        }


# Convenience factory functions
def create_notification_system(position: str = "top-right",
                               timeout: int = 5000,
                               max_notifications: int = 5) -> NotificationSystem:
    """Create a notification system with common settings."""
    try:
        pos = NotificationPosition(position)
    except ValueError:
        pos = NotificationPosition.TOP_RIGHT

    return NotificationSystem(position=pos, timeout=timeout, max_visible=max_notifications)


def add_notifications_to_map(folium_map: folium.Map, **kwargs) -> NotificationSystem:
    """Add notifications to a map (convenience function)."""
    system = create_notification_system(**kwargs)
    system.add_to_map(folium_map)
    return system
