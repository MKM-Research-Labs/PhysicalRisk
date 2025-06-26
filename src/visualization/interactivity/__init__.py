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
Interactivity modules for the visualization system.

This package contains modules for handling user interactions,
context menus, backend communication, JavaScript integration,
and user notifications.
"""

from .context_menus import ContextMenuHandler
from .backend_handler import BackendHandler
from .notifications import NotificationSystem, NotificationType, NotificationPosition
from .notifications import create_notification_system, add_notifications_to_map

# Convenience class for managing all interactivity components
class InteractivityManager:
    """
    Manages all interactivity components for map visualizations.
    
    This class provides a unified interface for adding context menus,
    backend communication, and notifications to maps.
    """
    
    def __init__(self, 
                 server_url: str = "http://127.0.0.1:5000",
                 notification_position: str = "top-right",
                 notification_timeout: int = 5000):
        """
        Initialize the interactivity manager.
        
        Args:
            server_url: Backend server URL
            notification_position: Position for notifications
            notification_timeout: Auto-dismiss timeout for notifications
        """
        self.context_menus = ContextMenuHandler()
        self.backend_handler = BackendHandler(server_url)
        self.notifications = create_notification_system(
            position=notification_position,
            timeout=notification_timeout
        )
    
    def setup_map_interactivity(self, folium_map):
        """
        Add all interactivity components to a Folium map.
        
        Args:
            folium_map: The Folium map to enhance with interactivity
        """
        print("🔧 Setting up map interactivity...")
        
        # Add notifications first (needed by other components)
        self.notifications.add_to_map(folium_map)
        
        # Add backend communication
        self.backend_handler.add_to_map(folium_map)
        
        # Add context menus
        self.context_menus.add_to_map(folium_map)
        
        print("✅ All interactivity components added to map")
        return self
    
    def configure(self, **kwargs):
        """
        Configure all interactivity components.
        
        Args:
            **kwargs: Configuration arguments for components
        """
        
        if 'server_url' in kwargs:
            self.backend_handler.configure(server_url=kwargs['server_url'])
        if 'notification_position' in kwargs:
            self.notifications.configure(position=kwargs['notification_position'])
        # Handle context menu configuration with proper parameter mapping
        if 'context_menu_gauge_items' in kwargs:
            self.context_menus.configure(gauge_menu_items=kwargs['context_menu_gauge_items'])
        
        # Handle backend configuration
        if 'backend_server_url' in kwargs:
            self.backend_handler.configure(server_url=kwargs['backend_server_url'])
        
        # Handle notification configuration
        if 'notification_timeout' in kwargs:
            self.notifications.configure(timeout=kwargs['notification_timeout'])
        if 'notification_position' in kwargs:
            self.notifications.configure(position=kwargs['notification_position'])
        if 'notification_max_notifications' in kwargs:
            self.notifications.configure(max_notifications=kwargs['notification_max_notifications'])
        
        return self
    
    def get_statistics(self):
        """
        Get statistics from all interactivity components.
        
        Returns:
            Dictionary with statistics from all components
        """
        return {
            'context_menus': self.context_menus.get_statistics(),
            'backend_handler': self.backend_handler.get_statistics(),
            'notifications': self.notifications.get_statistics()
        }


__all__ = [
    'ContextMenuHandler',
    'BackendHandler', 
    'NotificationSystem',
    'NotificationType',
    'NotificationPosition',
    'InteractivityManager',
    'create_notification_system',
    'add_notifications_to_map'
]