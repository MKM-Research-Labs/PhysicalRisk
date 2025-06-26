# Copyright (c) 2025 MKM Research Labs. All rights reserved.
# 
# This software is provided under license by MKM Research Labs. 
# Use, reproduction, distribution, or modification of this code is subject to the 
# terms and conditions of the license agreement provided with this software.
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

This module provides a comprehensive notification system for displaying
user feedback, status updates, and error messages in the map interface.
"""

from typing import Dict, Any, Optional, List, Literal
import folium
from enum import Enum


class NotificationType(Enum):
    """Enumeration of notification types."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    LOADING = "loading"


class NotificationPosition(Enum):
    """Enumeration of notification positions."""
    TOP_RIGHT = "top-right"
    TOP_LEFT = "top-left"
    TOP_CENTER = "top-center"
    BOTTOM_RIGHT = "bottom-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_CENTER = "bottom-center"


class NotificationSystem:
    """Comprehensive notification system for map interactions."""
    
    def __init__(self, 
                 default_position: NotificationPosition = NotificationPosition.TOP_RIGHT,
                 auto_dismiss_timeout: int = 5000,
                 max_notifications: int = 5):
        """
        Initialize the notification system.
        
        Args:
            default_position: Default position for notifications
            auto_dismiss_timeout: Auto-dismiss timeout in milliseconds
            max_notifications: Maximum number of notifications to show simultaneously
        """
        self.default_position = default_position
        self.auto_dismiss_timeout = auto_dismiss_timeout
        self.max_notifications = max_notifications
        
        # Predefined notification templates
        self.templates = {
            NotificationType.INFO: {
                "icon": "ℹ️",
                "color": "#2196F3",
                "background": "#E3F2FD"
            },
            NotificationType.SUCCESS: {
                "icon": "✅",
                "color": "#4CAF50",
                "background": "#E8F5E8"
            },
            NotificationType.WARNING: {
                "icon": "⚠️",
                "color": "#FF9800",
                "background": "#FFF3E0"
            },
            NotificationType.ERROR: {
                "icon": "❌",
                "color": "#f44336",
                "background": "#FFEBEE"
            },
            NotificationType.LOADING: {
                "icon": "🔄",
                "color": "#9E9E9E",
                "background": "#F5F5F5"
            }
        }
    
    def get_notification_js(self) -> str:
        """
        Get JavaScript code for notification system.
        
        Returns:
            JavaScript code as string
        """
        js_code = f"""
        <script>
        // Notification System Configuration
        const NOTIFICATION_CONFIG = {{
            defaultPosition: '{self.default_position.value}',
            autoDismissTimeout: {self.auto_dismiss_timeout},
            maxNotifications: {self.max_notifications},
            templates: {self._get_js_templates()}
        }};
        
        // Notification queue and management
        let notificationQueue = [];
        let notificationCounter = 0;
        
        // Main notification function
        function showNotification(message, type = 'info', options = {{}}) {{
            const notificationType = type.toLowerCase();
            const template = NOTIFICATION_CONFIG.templates[notificationType] || NOTIFICATION_CONFIG.templates.info;
            
            // Create notification object
            const notification = {{
                id: ++notificationCounter,
                message: message,
                type: notificationType,
                timestamp: new Date(),
                ...options
            }};
            
            // Add to queue and manage display
            addToQueue(notification);
            displayNotification(notification, template);
            
            return notification.id;
        }}
        
        // Add notification to queue and manage overflow
        function addToQueue(notification) {{
            notificationQueue.push(notification);
            
            // Remove oldest notifications if we exceed max
            while (notificationQueue.length > NOTIFICATION_CONFIG.maxNotifications) {{
                const oldestNotification = notificationQueue.shift();
                removeNotification(oldestNotification.id);
            }}
        }}
        
        // Display individual notification
        function displayNotification(notification, template) {{
            // Remove any existing notification with same ID
            removeNotification(notification.id);
            
            const container = getOrCreateNotificationContainer();
            const notificationElement = createNotificationElement(notification, template);
            
            container.appendChild(notificationElement);
            
            // Animate in
            setTimeout(() => {{
                notificationElement.classList.add('notification-show');
            }}, 10);
            
            // Auto-dismiss if enabled and not persistent
            if (NOTIFICATION_CONFIG.autoDismissTimeout > 0 && !notification.persistent) {{
                setTimeout(() => {{
                    dismissNotification(notification.id);
                }}, notification.timeout || NOTIFICATION_CONFIG.autoDismissTimeout);
            }}
        }}
        
        // Create notification element
        function createNotificationElement(notification, template) {{
            const element = document.createElement('div');
            element.id = 'notification-' + notification.id;
            element.className = 'map-notification notification-hide';
            
            // Determine if message contains newlines for formatting
            const hasNewlines = notification.message.includes('\\n');
            const messageDisplay = hasNewlines ? 
                notification.message.replace(/\\n/g, '<br>') : 
                notification.message;
            
            element.innerHTML = 
                '<div class="notification-content">' +
                    '<span class="notification-icon">' + template.icon + '</span>' +
                    '<div class="notification-text">' + messageDisplay + '</div>' +
                    '<button class="notification-close" onclick="dismissNotification(' + notification.id + ')">&times;</button>' +
                '</div>' +
                (notification.type === 'loading' ? '<div class="notification-progress"></div>' : '');
            
            // Apply styling
            element.style.cssText = 
                'background: ' + template.background + ';' +
                'border-left: 4px solid ' + template.color + ';' +
                'margin-bottom: 8px;' +
                'border-radius: 4px;' +
                'box-shadow: 0 2px 10px rgba(0,0,0,0.1);' +
                'font-family: Arial, sans-serif;' +
                'font-size: 14px;' +
                'max-width: 350px;' +
                'word-wrap: break-word;' +
                'opacity: 0;' +
                'transform: translateX(100%);' +
                'transition: all 0.3s ease;';
            
            // Add click-to-dismiss functionality
            element.addEventListener('click', (e) => {{
                if (!e.target.classList.contains('notification-close')) {{
                    dismissNotification(notification.id);
                }}
            }});
            
            return element;
        }}
        
        // Get or create notification container
        function getOrCreateNotificationContainer() {{
            let container = document.getElementById('notification-container');
            if (!container) {{
                container = document.createElement('div');
                container.id = 'notification-container';
                container.style.cssText = 
                    'position: fixed;' +
                    'z-index: 10000;' +
                    'pointer-events: none;' +
                    getPositionStyles(NOTIFICATION_CONFIG.defaultPosition);
                document.body.appendChild(container);
            }}
            return container;
        }}
        
        // Get position styles based on position
        function getPositionStyles(position) {{
            switch (position) {{
                case 'top-right':
                    return 'top: 20px; right: 20px;';
                case 'top-left':
                    return 'top: 20px; left: 20px;';
                case 'top-center':
                    return 'top: 20px; left: 50%; transform: translateX(-50%);';
                case 'bottom-right':
                    return 'bottom: 20px; right: 20px;';
                case 'bottom-left':
                    return 'bottom: 20px; left: 20px;';
                case 'bottom-center':
                    return 'bottom: 20px; left: 50%; transform: translateX(-50%);';
                default:
                    return 'top: 20px; right: 20px;';
            }}
        }}
        
        // Dismiss notification with animation
        function dismissNotification(notificationId) {{
            const element = document.getElementById('notification-' + notificationId);
            if (element) {{
                element.classList.remove('notification-show');
                element.classList.add('notification-hide');
                
                setTimeout(() => {{
                    removeNotification(notificationId);
                }}, 300);
            }}
        }}
        
        // Remove notification from DOM and queue
        function removeNotification(notificationId) {{
            const element = document.getElementById('notification-' + notificationId);
            if (element && element.parentNode) {{
                element.parentNode.removeChild(element);
            }}
            
            // Remove from queue
            notificationQueue = notificationQueue.filter(n => n.id !== notificationId);
        }}
        
        // Clear all notifications
        function clearAllNotifications() {{
            notificationQueue.forEach(notification => {{
                removeNotification(notification.id);
            }});
            notificationQueue = [];
        }}
        
        // Update notification (useful for progress updates)
        function updateNotification(notificationId, newMessage, newType) {{
            const element = document.getElementById('notification-' + notificationId);
            if (element) {{
                const textElement = element.querySelector('.notification-text');
                const iconElement = element.querySelector('.notification-icon');
                
                if (textElement) {{
                    textElement.innerHTML = newMessage.replace(/\\n/g, '<br>');
                }}
                
                if (newType && iconElement) {{
                    const template = NOTIFICATION_CONFIG.templates[newType] || NOTIFICATION_CONFIG.templates.info;
                    iconElement.textContent = template.icon;
                    element.style.background = template.background;
                    element.style.borderLeftColor = template.color;
                }}
            }}
        }}
        
        // Specialized notification functions
        function showSuccessNotification(message, options = {{}}) {{
            return showNotification(message, 'success', options);
        }}
        
        function showErrorNotification(message, options = {{}}) {{
            return showNotification(message, 'error', {{...options, persistent: true}});
        }}
        
        function showWarningNotification(message, options = {{}}) {{
            return showNotification(message, 'warning', options);
        }}
        
        function showInfoNotification(message, options = {{}}) {{
            return showNotification(message, 'info', options);
        }}
        
        function showLoadingNotification(message, options = {{}}) {{
            return showNotification(message, 'loading', {{...options, persistent: true}});
        }}
        
        // Progress notification management
        function showProgressNotification(message, progress = 0) {{
            const notificationId = showLoadingNotification(message);
            updateProgress(notificationId, progress);
            return notificationId;
        }}
        
        function updateProgress(notificationId, progress) {{
            const element = document.getElementById('notification-' + notificationId);
            if (element) {{
                let progressBar = element.querySelector('.notification-progress');
                if (!progressBar) {{
                    progressBar = document.createElement('div');
                    progressBar.className = 'notification-progress';
                    progressBar.style.cssText = 
                        'height: 3px;' +
                        'background: #e0e0e0;' +
                        'margin-top: 8px;' +
                        'border-radius: 2px;' +
                        'overflow: hidden;';
                    
                    const progressFill = document.createElement('div');
                    progressFill.className = 'notification-progress-fill';
                    progressFill.style.cssText = 
                        'height: 100%;' +
                        'background: #2196F3;' +
                        'width: 0%;' +
                        'transition: width 0.3s ease;';
                    
                    progressBar.appendChild(progressFill);
                    element.appendChild(progressBar);
                }}
                
                const progressFill = progressBar.querySelector('.notification-progress-fill');
                if (progressFill) {{
                    progressFill.style.width = Math.max(0, Math.min(100, progress)) + '%';
                }}
            }}
        }}
        
        // Add CSS styles
        function addNotificationStyles() {{
            const styleSheet = document.createElement('style');
            styleSheet.textContent = 
                '.map-notification {{' +
                    'pointer-events: auto;' +
                    'padding: 12px 16px;' +
                    'margin-bottom: 8px;' +
                    'border-radius: 4px;' +
                    'transition: all 0.3s ease;' +
                '}}' +
                '.notification-content {{' +
                    'display: flex;' +
                    'align-items: flex-start;' +
                    'gap: 8px;' +
                '}}' +
                '.notification-icon {{' +
                    'font-size: 16px;' +
                    'flex-shrink: 0;' +
                    'margin-top: 1px;' +
                '}}' +
                '.notification-text {{' +
                    'flex-grow: 1;' +
                    'line-height: 1.4;' +
                '}}' +
                '.notification-close {{' +
                    'background: none;' +
                    'border: none;' +
                    'font-size: 18px;' +
                    'cursor: pointer;' +
                    'color: #666;' +
                    'padding: 0;' +
                    'margin-left: 8px;' +
                    'flex-shrink: 0;' +
                '}}' +
                '.notification-close:hover {{' +
                    'color: #333;' +
                '}}' +
                '.notification-show {{' +
                    'opacity: 1 !important;' +
                    'transform: translateX(0) !important;' +
                '}}' +
                '.notification-hide {{' +
                    'opacity: 0 !important;' +
                    'transform: translateX(100%) !important;' +
                '}}' +
                '@keyframes spin {{' +
                    'from {{ transform: rotate(0deg); }}' +
                    'to {{ transform: rotate(360deg); }}' +
                '}}' +
                '.map-notification[class*="loading"] .notification-icon {{' +
                    'animation: spin 1s linear infinite;' +
                '}}';
            document.head.appendChild(styleSheet);
        }}
        
        // Initialize notification system
        function initializeNotificationSystem() {{
            console.log('Notification system initialized');
            addNotificationStyles();
            
            // Test notification on initialization (optional)
            // showInfoNotification('Notification system ready!', {{ timeout: 2000 }});
        }}
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', initializeNotificationSystem);
        }} else {{
            initializeNotificationSystem();
        }}
        </script>
        """
        
        return js_code
    
    def _get_js_templates(self) -> str:
        """
        Convert Python templates to JavaScript object.
        
        Returns:
            JavaScript object string
        """
        js_templates = {}
        for notification_type, template in self.templates.items():
            js_templates[notification_type.value] = template
        
        return str(js_templates).replace("'", '"')
    
    def add_to_map(self, folium_map: folium.Map) -> None:
        """
        Add notification system to a Folium map.
        
        Args:
            folium_map: The Folium map to add notifications to
        """
        # Add the notification JavaScript
        notification_js = self.get_notification_js()
        folium_map.get_root().html.add_child(folium.Element(notification_js))
        
        print("✅ Notification system added to map")
    
    def configure(self, 
                 position: Optional[NotificationPosition] = None,
                 timeout: Optional[int] = None,
                 max_notifications: Optional[int] = None,
                 custom_templates: Optional[Dict[NotificationType, Dict[str, str]]] = None) -> None:
        """
        Configure notification system settings.
        
        Args:
            position: Default position for notifications
            timeout: Auto-dismiss timeout in milliseconds
            max_notifications: Maximum number of notifications
            custom_templates: Custom notification templates
        """
        if position:
            self.default_position = position
        
        if timeout is not None:
            self.auto_dismiss_timeout = timeout
        
        if max_notifications is not None:
            self.max_notifications = max_notifications
        
        if custom_templates:
            self.templates.update(custom_templates)
        
        print("✅ Notification system configured")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about notification system configuration.
        
        Returns:
            Dictionary with notification system statistics
        """
        return {
            'default_position': self.default_position.value,
            'auto_dismiss_timeout': self.auto_dismiss_timeout,
            'max_notifications': self.max_notifications,
            'available_types': [t.value for t in NotificationType],
            'available_positions': [p.value for p in NotificationPosition],
            'template_count': len(self.templates)
        }
    
    def create_predefined_notifications(self) -> Dict[str, str]:
        """
        Create a set of predefined notification messages for common scenarios.
        
        Returns:
            Dictionary mapping scenario names to notification messages
        """
        return {
            'report_generation_started': "📄 Generating property report...",
            'report_generation_success': "✅ Property report generated successfully!",
            'report_generation_error': "❌ Failed to generate property report",
            'gauge_report_started': "📊 Generating gauge report...",
            'gauge_report_success': "✅ Gauge report generated successfully!",
            'gauge_report_error': "❌ Failed to generate gauge report",
            'data_export_started': "💾 Exporting data...",
            'data_export_success': "✅ Data exported successfully!",
            'data_export_error': "❌ Failed to export data",
            'server_connection_error': "🔌 Cannot connect to server. Please check if the backend is running.",
            'server_timeout': "⏱️ Request timed out. Please try again.",
            'cors_error': "🚫 CORS Error: Server needs CORS configuration",
            'map_ready': "🗺️ Interactive map ready!",
            'feature_not_available': "🚧 This feature is coming soon!",
            'invalid_selection': "⚠️ Please select a valid item first",
            'operation_cancelled': "🛑 Operation cancelled by user",
            'data_loading': "📂 Loading data...",
            'data_loaded': "✅ Data loaded successfully!",
            'data_error': "❌ Error loading data"
        }


# Convenience functions for quick notification creation
def create_notification_system(position: str = "top-right", 
                             timeout: int = 5000,
                             max_notifications: int = 5) -> NotificationSystem:
    """
    Create a notification system with common settings.
    
    Args:
        position: Position for notifications
        timeout: Auto-dismiss timeout
        max_notifications: Maximum notifications
        
    Returns:
        Configured NotificationSystem instance
    """
    try:
        pos_enum = NotificationPosition(position)
    except ValueError:
        pos_enum = NotificationPosition.TOP_RIGHT
    
    return NotificationSystem(
        default_position=pos_enum,
        auto_dismiss_timeout=timeout,
        max_notifications=max_notifications
    )


def add_notifications_to_map(folium_map: folium.Map, **kwargs) -> NotificationSystem:
    """
    Convenience function to add notifications to a map.
    
    Args:
        folium_map: Folium map to add notifications to
        **kwargs: Configuration arguments for NotificationSystem
        
    Returns:
        The configured NotificationSystem instance
    """
    notification_system = create_notification_system(**kwargs)
    notification_system.add_to_map(folium_map)
    return notification_system