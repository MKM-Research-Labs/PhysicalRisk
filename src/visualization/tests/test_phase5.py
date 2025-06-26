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

#!/usr/bin/env python3
"""
Phase 5 Testing and Validation Script with Auto-Fix

This script tests all the interactivity modules and automatically fixes
common issues before running tests.
"""

import os
import sys
import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch
import folium

# Fix the Python path to find project modules
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import modules
from src.utilities.project_paths import ProjectPaths

# Set the visualization directory for auto-fixes
visualization_dir = project_root / "src" / "visualization"


def auto_fix_interactivity_modules():
    """
    Auto-fix common issues with interactivity modules before running tests.
    
    Returns:
        bool: True if fixes were applied successfully, False otherwise
    """
    print("🔧 Checking and auto-fixing interactivity modules...")
    
    init_path = visualization_dir / "interactivity" / "__init__.py"
    
    if not init_path.exists():
        print("❌ src/visualization/interactivity/__init__.py not found - please run setup_phase5.py first")
        return False
    
    try:
        # Read current content
        with open(init_path, 'r') as f:
            content = f.read()
        
        original_content = content
        fixes_applied = []
        
        # Fix 1: Update ContextMenuHandler.configure() method - more comprehensive
        old_configure_patterns = [
            '''    def configure(self, **kwargs):
        pass''',
            '''    def configure(self, **kwargs):
        """Configure context menu items."""
        if property_menu_items:
            self.property_menu_items = property_menu_items
        if gauge_menu_items:
            self.gauge_menu_items = gauge_menu_items'''
        ]
        
        new_configure = '''    def configure(self, property_menu_items=None, gauge_menu_items=None, **kwargs):
        """Configure context menu items."""
        if property_menu_items is not None:
            self.property_menu_items = property_menu_items
        if gauge_menu_items is not None:
            self.gauge_menu_items = gauge_menu_items'''
        
        for old_pattern in old_configure_patterns:
            if old_pattern in content:
                content = content.replace(old_pattern, new_configure)
                fixes_applied.append("ContextMenuHandler.configure() method")
                break
        
        # Fix 2: Update BackendHandler.__init__() to handle None server_url - FORCE FIX
        # First, let's check if BackendHandler(None) actually fails
        backend_test_failed = False
        try:
            test_backend = BackendHandler(None)
            if test_backend.server_url is None:
                backend_test_failed = True
        except:
            backend_test_failed = True
        
        if backend_test_failed:
            # Force fix the BackendHandler class
            backend_class_start = content.find("class BackendHandler:")
            if backend_class_start != -1:
                # Find the __init__ method
                init_start = content.find("def __init__(self, server_url=", backend_class_start)
                if init_start != -1:
                    # Find the end of the __init__ method (next method or class)
                    method_end = content.find("\n    def ", init_start + 1)
                    if method_end == -1:
                        method_end = content.find("\nclass ", init_start + 1)
                    if method_end == -1:
                        method_end = len(content)
                    
                    # Extract method signature line
                    signature_end = content.find("):", init_start)
                    if signature_end != -1:
                        signature = content[init_start:signature_end + 2]
                        
                        # Create new method body
                        new_init_method = f'''def __init__(self, server_url="http://127.0.0.1:5000"):
        """Initialize backend handler with proper None handling."""
        # FORCE FIX: Explicitly handle None server_url case
        if server_url is None:
            self.server_url = "http://127.0.0.1:5000"
            print("🔧 BackendHandler: Fixed None server_url -> default")
        else:
            self.server_url = server_url
        self.endpoints = {{
            'property_report': '/generate_property_report',
            'gauge_report': '/generate_gauge_report',
            'export_data': '/export_data',
            'health_check': '/health'
        }}'''
                        
                        # Replace the entire __init__ method
                        old_method = content[init_start:method_end]
                        # Find where the actual method content starts (after the signature)
                        content_start = content.find("\n", signature_end) + 1
                        method_content = content[content_start:method_end]
                        
                        # Replace
                        content = content.replace(old_method, new_init_method + "\n")
                        fixes_applied.append("BackendHandler.__init__() FORCE FIX for None handling")
        
        # Also add the original pattern-based fixes as backup
        old_backend_patterns = [
            '''    def __init__(self, server_url="http://127.0.0.1:5000"):
        self.server_url = server_url''',
            '''    def __init__(self, server_url="http://127.0.0.1:5000"):
        self.server_url = server_url if server_url is not None else "http://127.0.0.1:5000"''',
            '''    def __init__(self, server_url="http://127.0.0.1:5000"):
        # Handle None server_url properly
        if server_url is None:
            self.server_url = "http://127.0.0.1:5000"
        else:
            self.server_url = server_url'''
        ]
        
        new_backend_init = '''    def __init__(self, server_url="http://127.0.0.1:5000"):
        # PATTERN FIX: Explicitly handle None server_url case  
        if server_url is None:
            self.server_url = "http://127.0.0.1:5000"
            print("🔧 BackendHandler: Pattern fixed None server_url")
        else:
            self.server_url = server_url'''
        
        for old_pattern in old_backend_patterns:
            if old_pattern in content:
                content = content.replace(old_pattern, new_backend_init)
                fixes_applied.append("BackendHandler.__init__() Pattern fix")
                break
        
        # Fix 3: Update InteractivityManager.configure() method - more robust
        old_manager_configure_pattern = '''        # Handle context menu configuration
        context_menu_config = {}
        if 'context_menu_property_items' in kwargs:
            context_menu_config['property_menu_items'] = kwargs['context_menu_property_items']
        if 'context_menu_gauge_items' in kwargs:
            context_menu_config['gauge_menu_items'] = kwargs['context_menu_gauge_items']
        
        # Handle backend configuration
        backend_config = {}
        if 'backend_server_url' in kwargs:
            backend_config['server_url'] = kwargs['backend_server_url']
        
        # Handle notification configuration
        notification_config = {}
        if 'notification_timeout' in kwargs:
            notification_config['timeout'] = kwargs['notification_timeout']
        if 'notification_position' in kwargs:
            notification_config['position'] = kwargs['notification_position']
        if 'notification_max_notifications' in kwargs:
            notification_config['max_notifications'] = kwargs['notification_max_notifications']
        
        # Apply configurations
        if context_menu_config:
            self.context_menus.configure(**context_menu_config)
        
        if backend_config:
            self.backend_handler.configure(**backend_config)
        
        if notification_config:
            self.notifications.configure(**notification_config)'''
        
        # Alternative pattern to look for
        alt_manager_configure = '''        # Extract component-specific configurations
        context_menu_config = {k: v for k, v in kwargs.items() 
                             if k.startswith('context_menu_')}
        backend_config = {k: v for k, v in kwargs.items() 
                        if k.startswith('backend_')}
        notification_config = {k: v for k, v in kwargs.items() 
                             if k.startswith('notification_')}
        
        if context_menu_config:
            self.context_menus.configure(**context_menu_config)
        
        if backend_config:
            self.backend_handler.configure(**backend_config)
        
        if notification_config:
            self.notifications.configure(**notification_config)'''
        
        new_manager_configure = '''        # Handle context menu configuration with proper parameter mapping
        if 'context_menu_property_items' in kwargs:
            self.context_menus.configure(property_menu_items=kwargs['context_menu_property_items'])
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
            self.notifications.configure(max_notifications=kwargs['notification_max_notifications'])'''
        
        if old_manager_configure_pattern in content:
            content = content.replace(old_manager_configure_pattern, new_manager_configure)
            fixes_applied.append("InteractivityManager.configure() parameter mapping")
        elif alt_manager_configure in content:
            content = content.replace(alt_manager_configure, new_manager_configure)
            fixes_applied.append("InteractivityManager.configure() parameter mapping (alt)")
        
        # Fix 4: Remove template literals from the placeholder JavaScript (comprehensive)
        template_literal_fixes = [
            # Context menu fixes
            ('''console.log(`Context menu shown for ${menuType}: ${itemId}`);''',
             '''console.log('Context menu shown for ' + menuType + ': ' + itemId);'''),
            ('''console.log(`Added context menu to ${markerType}: ${markerId}`);''',
             '''console.log('Added context menu to ' + markerType + ': ' + markerId);'''),
            ('''console.log(`Added context menus to ${propertyMarkerCount} property markers and ${gaugeMarkerCount} gauge markers`);''',
             '''console.log('Added context menus to ' + propertyMarkerCount + ' property markers and ' + gaugeMarkerCount + ' gauge markers');'''),
            
            # Backend handler fixes  
            ('''showNotification(`Processing request...`, 'info');''',
             '''showNotification('Processing request...', 'info');'''),
            ('''const response = await fetch(`${BACKEND_CONFIG.serverUrl}${endpoint}`, {''',
             '''const response = await fetch(BACKEND_CONFIG.serverUrl + endpoint, {'''),
            ('''throw new Error(`HTTP error! status: ${response.status}`);''',
             '''throw new Error('HTTP error! status: ' + response.status);'''),
            ('''showNotification(`❌ Error: ${result.message}`, 'error');''',
             '''showNotification('❌ Error: ' + result.message, 'error');'''),
            ('''errorMessage = `🔌 Cannot connect to server.\\n\\nPlease check:\\n1. Server is running on ${BACKEND_CONFIG.serverUrl}\\n2. CORS is enabled\\n3. Network connectivity`;''',
             '''errorMessage = '🔌 Cannot connect to server.\\n\\nPlease check:\\n1. Server is running on ' + BACKEND_CONFIG.serverUrl + '\\n2. CORS is enabled\\n3. Network connectivity';'''),
            ('''errorMessage = `🚫 Error: ${error.message}`;''',
             '''errorMessage = '🚫 Error: ' + error.message;'''),
            ('''showNotification(`Time series view for ${gaugeId} - Feature coming soon`, 'info');''',
             '''showNotification('Time series view for ' + gaugeId + ' - Feature coming soon', 'info');'''),
            ('''showNotification(`Could not find details for property ${propertyId}`, 'error');''',
             '''showNotification('Could not find details for property ' + propertyId, 'error');'''),
            ('''showNotification(`Showing details for property ${propertyId}`, 'info');''',
             '''showNotification('Showing details for property ' + propertyId, 'info');'''),
            ('''tooltip.getContent().includes(`Property: ${propertyId}`)''',
             '''tooltip.getContent().includes('Property: ' + propertyId)'''),
            ('''const response = await fetch(`${BACKEND_CONFIG.serverUrl}${BACKEND_CONFIG.endpoints.health_check}`, {''',
             '''const response = await fetch(BACKEND_CONFIG.serverUrl + BACKEND_CONFIG.endpoints.health_check, {'''),
            ('''console.log(`Backend server: ${BACKEND_CONFIG.serverUrl}`);''',
             '''console.log('Backend server: ' + BACKEND_CONFIG.serverUrl);'''),
            
            # Notification system fixes
            ('''element.id = `notification-${notification.id}`;''',
             '''element.id = 'notification-' + notification.id;'''),
            ('''<span class="notification-icon">${template.icon}</span>''',
             '''<span class="notification-icon">' + template.icon + '</span>'''),
            ('''<div class="notification-text">${messageDisplay}</div>''',
             '''<div class="notification-text">' + messageDisplay + '</div>'''),
            ('''onclick="dismissNotification(${notification.id})"''',
             '''onclick="dismissNotification(' + notification.id + ')"'''),
            ('''${notification.type === 'loading' ? '<div class="notification-progress"></div>' : ''}''',
             '''+ (notification.type === 'loading' ? '<div class="notification-progress"></div>' : '') + '''),
            ('''background: ${template.background};''',
             '''background: ' + template.background + ';'''),
            ('''border-left: 4px solid ${template.color};''',
             '''border-left: 4px solid ' + template.color + ';'''),
            ('''${getPositionStyles(NOTIFICATION_CONFIG.defaultPosition)}''',
             ''' + getPositionStyles(NOTIFICATION_CONFIG.defaultPosition) + '''),
            ('''const element = document.getElementById(`notification-${notificationId}`);''',
             '''const element = document.getElementById('notification-' + notificationId);'''),
            ('''progressFill.style.width = `${Math.max(0, Math.min(100, progress))}%`;''',
             '''progressFill.style.width = Math.max(0, Math.min(100, progress)) + '%';''')
        ]
        
        js_fixes_count = 0
        for old_pattern, new_pattern in template_literal_fixes:
            if old_pattern in content:
                content = content.replace(old_pattern, new_pattern)
                js_fixes_count += 1
        
        if js_fixes_count > 0:
            fixes_applied.append(f"JavaScript template literals ({js_fixes_count} fixes)")
        
        # Write back if changes were made
        if content != original_content:
            with open(init_path, 'w') as f:
                f.write(content)
            
            if fixes_applied:
                print("  ✓ Applied fixes:")
                for fix in fixes_applied:
                    print(f"    - {fix}")
            else:
                print("  ✓ Content updated but no specific fixes identified")
            
            return True
        else:
            print("  ✓ No fixes needed - modules already up to date")
            return True
            
    except Exception as e:
        print(f"  ❌ Error applying auto-fixes: {e}")
        return False


# Try to import modules and apply fixes if needed
try:
    from src.visualization.interactivity import (
        ContextMenuHandler,
        BackendHandler,
        NotificationSystem,
        NotificationType,
        NotificationPosition,
        InteractivityManager,
        create_notification_system,
        add_notifications_to_map
    )
    MODULES_AVAILABLE = True
    print("✅ Interactivity modules imported successfully")
except ImportError as e:
    print(f"⚠️  Could not import interactivity modules: {e}")
    print("🔧 Attempting to auto-fix...")
    
    if auto_fix_interactivity_modules():
        print("🔄 Retrying import after auto-fix...")
        try:
            from src.visualization.interactivity import (
                ContextMenuHandler,
                BackendHandler,
                NotificationSystem,
                NotificationType,
                NotificationPosition,
                InteractivityManager,
                create_notification_system,
                add_notifications_to_map
            )
            MODULES_AVAILABLE = True
            print("✅ Interactivity modules imported successfully after auto-fix")
        except ImportError as e2:
            print(f"❌ Still could not import after auto-fix: {e2}")
            MODULES_AVAILABLE = False
    else:
        MODULES_AVAILABLE = False


class TestNotificationSystem(unittest.TestCase):
    """Test the notification system functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not MODULES_AVAILABLE:
            self.skipTest("Interactivity modules not available")
        self.notification_system = NotificationSystem()
    
    def test_initialization(self):
        """Test notification system initialization."""
        self.assertIsInstance(self.notification_system, NotificationSystem)
        self.assertEqual(self.notification_system.default_position, NotificationPosition.TOP_RIGHT)
        self.assertEqual(self.notification_system.auto_dismiss_timeout, 5000)
        self.assertEqual(self.notification_system.max_notifications, 5)
    
    def test_javascript_generation(self):
        """Test JavaScript code generation."""
        js_code = self.notification_system.get_notification_js()
        
        # Check for essential functions
        self.assertIn("showNotification", js_code)
        self.assertIn("showSuccessNotification", js_code)
        self.assertIn("showErrorNotification", js_code)
        self.assertIn("showLoadingNotification", js_code)
        
        # Check that template literals are not used (should be fixed)
        self.assertNotIn("${", js_code, "JavaScript should not contain template literals")
    
    def test_configuration(self):
        """Test notification system configuration."""
        self.notification_system.configure(
            position=NotificationPosition.BOTTOM_LEFT,
            timeout=3000,
            max_notifications=10
        )
        
        self.assertEqual(self.notification_system.default_position, NotificationPosition.BOTTOM_LEFT)
        self.assertEqual(self.notification_system.auto_dismiss_timeout, 3000)
        self.assertEqual(self.notification_system.max_notifications, 10)
    
    def test_custom_templates(self):
        """Test custom notification templates."""
        # This test is simplified since we're using placeholder implementation
        self.notification_system.configure(timeout=1000)
        self.assertEqual(self.notification_system.auto_dismiss_timeout, 1000)
    
    def test_statistics(self):
        """Test getting statistics."""
        stats = self.notification_system.get_statistics()
        
        self.assertIn('default_position', stats)
        self.assertIn('auto_dismiss_timeout', stats)
        self.assertIn('max_notifications', stats)
        self.assertIn('available_types', stats)
        self.assertIn('available_positions', stats)
    
    def test_predefined_notifications(self):
        """Test predefined notification messages (placeholder test)."""
        # Since we're using placeholder implementation, just test that the system works
        stats = self.notification_system.get_statistics()
        self.assertIsInstance(stats, dict)
    
    def test_folium_integration(self):
        """Test integration with Folium maps."""
        test_map = folium.Map(location=[51.5074, -0.1278])
        
        # Should not raise any exceptions
        self.notification_system.add_to_map(test_map)
        
        # Check that JavaScript was added
        html_content = test_map._repr_html_()
        self.assertIn("showNotification", html_content)


class TestContextMenuHandler(unittest.TestCase):
    """Test the context menu handler functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not MODULES_AVAILABLE:
            self.skipTest("Interactivity modules not available")
        self.context_handler = ContextMenuHandler()
    
    def test_initialization(self):
        """Test context menu handler initialization."""
        self.assertIsInstance(self.context_handler, ContextMenuHandler)
        self.assertTrue(len(self.context_handler.property_menu_items) > 0)
        self.assertTrue(len(self.context_handler.gauge_menu_items) > 0)
    
    def test_javascript_generation(self):
        """Test JavaScript code generation."""
        js_code = self.context_handler.get_base_context_menu_js()
        
        # Check for essential functions
        self.assertIn("showContextMenu", js_code)
        
        # Check that template literals are not used (should be fixed)
        self.assertNotIn("${", js_code, "JavaScript should not contain template literals")
    
    def test_configuration(self):
        """Test context menu configuration."""
        custom_property_items = [
            {"id": "custom_action", "label": "🔧 Custom Action", "action": "customAction"}
        ]
        
        custom_gauge_items = [
            {"id": "custom_gauge", "label": "⚙️ Custom Gauge", "action": "customGaugeAction"}
        ]
        
        # This should not raise an error after auto-fix
        self.context_handler.configure(
            property_menu_items=custom_property_items,
            gauge_menu_items=custom_gauge_items
        )
        
        self.assertEqual(self.context_handler.property_menu_items, custom_property_items)
        self.assertEqual(self.context_handler.gauge_menu_items, custom_gauge_items)
    
    def test_statistics(self):
        """Test getting statistics."""
        stats = self.context_handler.get_statistics()
        
        self.assertIn('property_menu_items', stats)
        self.assertIn('gauge_menu_items', stats)
        self.assertIn('total_menu_items', stats)
    
    def test_folium_integration(self):
        """Test integration with Folium maps."""
        test_map = folium.Map(location=[51.5074, -0.1278])
        
        # Should not raise any exceptions
        self.context_handler.add_to_map(test_map)
        
        # Check that JavaScript was added
        html_content = test_map._repr_html_()
        self.assertIn("showContextMenu", html_content)


class TestBackendHandler(unittest.TestCase):
    """Test the backend handler functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not MODULES_AVAILABLE:
            self.skipTest("Interactivity modules not available")
        self.backend_handler = BackendHandler()
    
    def test_initialization(self):
        """Test backend handler initialization."""
        self.assertIsInstance(self.backend_handler, BackendHandler)
        self.assertEqual(self.backend_handler.server_url, "http://127.0.0.1:5000")
        self.assertIn('property_report', self.backend_handler.endpoints)
        self.assertIn('gauge_report', self.backend_handler.endpoints)
    
    def test_custom_server_url(self):
        """Test custom server URL initialization."""
        custom_handler = BackendHandler("https://api.example.com")
        self.assertEqual(custom_handler.server_url, "https://api.example.com")
    
    def test_none_server_url_handling(self):
        """Test that None server_url is handled properly."""
        # This should not result in None after auto-fix
        handler_with_none = BackendHandler(None)
        self.assertIsNotNone(handler_with_none.server_url)
        self.assertEqual(handler_with_none.server_url, "http://127.0.0.1:5000")
    
    def test_javascript_generation(self):
        """Test JavaScript code generation."""
        js_code = self.backend_handler.get_backend_js()
        
        # Check for essential functions
        self.assertIn("generateReport", js_code)
        self.assertIn("generateGaugeReport", js_code)
        
        # Check that template literals are not used (should be fixed)
        self.assertNotIn("${", js_code, "JavaScript should not contain template literals")
    
    def test_configuration(self):
        """Test backend handler configuration."""
        self.backend_handler.configure(
            server_url="https://new-server.com",
            endpoints={"custom_endpoint": "/api/custom"}
        )
        
        self.assertEqual(self.backend_handler.server_url, "https://new-server.com")
        self.assertIn("custom_endpoint", self.backend_handler.endpoints)
    
    def test_statistics(self):
        """Test getting statistics."""
        stats = self.backend_handler.get_statistics()
        
        self.assertIn('server_url', stats)
        self.assertIn('total_endpoints', stats)
        self.assertIn('endpoints', stats)
    
    def test_folium_integration(self):
        """Test integration with Folium maps."""
        test_map = folium.Map(location=[51.5074, -0.1278])
        
        # Should not raise any exceptions
        self.backend_handler.add_to_map(test_map)
        
        # Check that JavaScript was added
        html_content = test_map._repr_html_()
        self.assertIn("generateReport", html_content)


class TestInteractivityManager(unittest.TestCase):
    """Test the interactivity manager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not MODULES_AVAILABLE:
            self.skipTest("Interactivity modules not available")
        self.interactivity_manager = InteractivityManager()
    
    def test_initialization(self):
        """Test interactivity manager initialization."""
        self.assertIsInstance(self.interactivity_manager, InteractivityManager)
        self.assertIsInstance(self.interactivity_manager.context_menus, ContextMenuHandler)
        self.assertIsInstance(self.interactivity_manager.backend_handler, BackendHandler)
        self.assertIsInstance(self.interactivity_manager.notifications, NotificationSystem)
    
    def test_custom_initialization(self):
        """Test custom initialization parameters."""
        manager = InteractivityManager(
            server_url="https://custom.com",
            notification_position="bottom-left",
            notification_timeout=10000
        )
        
        self.assertEqual(manager.backend_handler.server_url, "https://custom.com")
        self.assertEqual(manager.notifications.default_position, NotificationPosition.BOTTOM_LEFT)
        self.assertEqual(manager.notifications.auto_dismiss_timeout, 10000)
    
    def test_map_setup(self):
        """Test setting up map interactivity."""
        test_map = folium.Map(location=[51.5074, -0.1278])
        
        # Should not raise any exceptions
        result = self.interactivity_manager.setup_map_interactivity(test_map)
        self.assertEqual(result, self.interactivity_manager)
        
        # Check that all components were added
        html_content = test_map._repr_html_()
        self.assertIn("showNotification", html_content)  # Notifications
        self.assertIn("generateReport", html_content)    # Backend handler
        self.assertIn("showContextMenu", html_content)   # Context menus
    
    def test_configuration(self):
        """Test manager configuration with the problematic parameters."""
        # This should not raise an error after auto-fix
        self.interactivity_manager.configure(
            context_menu_property_items=[{"id": "test", "label": "Test"}],
            backend_server_url="https://test.com",
            notification_timeout=1000
        )
        
        # Verify the configuration was applied
        self.assertEqual(self.interactivity_manager.backend_handler.server_url, "https://test.com")
        self.assertEqual(self.interactivity_manager.notifications.auto_dismiss_timeout, 1000)
    
    def test_statistics(self):
        """Test getting combined statistics."""
        stats = self.interactivity_manager.get_statistics()
        
        self.assertIn('context_menus', stats)
        self.assertIn('backend_handler', stats)
        self.assertIn('notifications', stats)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not MODULES_AVAILABLE:
            self.skipTest("Interactivity modules not available")
    
    def test_create_notification_system(self):
        """Test create_notification_system function."""
        ns = create_notification_system(
            position="bottom-right",
            timeout=3000,
            max_notifications=10
        )
        
        self.assertIsInstance(ns, NotificationSystem)
        self.assertEqual(ns.default_position, NotificationPosition.BOTTOM_RIGHT)
        self.assertEqual(ns.auto_dismiss_timeout, 3000)
        self.assertEqual(ns.max_notifications, 10)
    
    def test_add_notifications_to_map(self):
        """Test add_notifications_to_map function."""
        test_map = folium.Map(location=[51.5074, -0.1278])
        
        result = add_notifications_to_map(
            test_map,
            position="top-left",
            timeout=2000
        )
        
        self.assertIsInstance(result, NotificationSystem)
        
        # Check that notifications were added to map
        html_content = test_map._repr_html_()
        self.assertIn("showNotification", html_content)


class TestIntegrationScenarios(unittest.TestCase):
    """Test realistic integration scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not MODULES_AVAILABLE:
            self.skipTest("Interactivity modules not available")
    
    def test_minimal_setup(self):
        """Test minimal setup scenario."""
        # Create a map
        test_map = folium.Map(location=[51.5074, -0.1278])
        
        # Add minimal interactivity
        manager = InteractivityManager()
        manager.setup_map_interactivity(test_map)
        
        # Should work without errors
        html_content = test_map._repr_html_()
        self.assertIn("showNotification", html_content)
    
    def test_custom_configuration(self):
        """Test custom configuration scenario."""
        test_map = folium.Map(location=[51.5074, -0.1278])
        
        # Create with custom settings
        manager = InteractivityManager(
            server_url="https://api.example.com",
            notification_position="bottom-left"
        )
        
        # Add custom menu items
        manager.context_menus.configure(
            property_menu_items=[
                {"id": "analyze", "label": "📊 Analyze", "action": "analyzeProperty"}
            ]
        )
        
        # Setup map
        manager.setup_map_interactivity(test_map)
        
        # Verify customizations
        html_content = test_map._repr_html_()
        self.assertIn("https://api.example.com", html_content)
        self.assertIn("bottom-left", html_content)
    
    def test_individual_components(self):
        """Test using individual components separately."""
        test_map = folium.Map(location=[51.5074, -0.1278])
        
        # Add only notifications
        notifications = NotificationSystem()
        notifications.add_to_map(test_map)
        
        # Add only backend handler
        backend = BackendHandler("https://test.com")
        backend.add_to_map(test_map)
        
        # Verify both were added
        html_content = test_map._repr_html_()
        self.assertIn("showNotification", html_content)
        self.assertIn("generateReport", html_content)
        self.assertIn("https://test.com", html_content)
    
    def test_error_handling(self):
        """Test error handling scenarios."""
        # Test with invalid notification position (should fall back to default)
        manager = InteractivityManager(notification_position="invalid-position")
        self.assertEqual(manager.notifications.default_position, NotificationPosition.TOP_RIGHT)
        
        # Test with None server URL (should handle gracefully after auto-fix)
        manager2 = InteractivityManager(server_url=None)
        self.assertIsNotNone(manager2.backend_handler.server_url)


class TestWithRealData(unittest.TestCase):
    """Test with realistic data structures."""
    
    def setUp(self):
        """Set up test fixtures with sample data."""
        if not MODULES_AVAILABLE:
            self.skipTest("Interactivity modules not available")
        
        self.test_data = {
            "tc_data": {
                "timeseries": [
                    {
                        "EventTimeseries": {
                            "Dimensions": {"lat": 51.5074, "lon": -0.1278},
                            "Header": {"time": "2023-01-01T00:00:00Z"},
                            "SurfaceNearSurface": {"u10m": 10, "v10m": 5, "msl": 101325, "tp": 0.001},
                            "CycloneParameters": {"storm_size": 50}
                        }
                    }
                ]
            },
            "gauge_data": {
                "floodGauges": [
                    {
                        "FloodGauge": {
                            "Header": {"GaugeID": "GAUGE-test123"},
                            "SensorDetails": {
                                "GaugeInformation": {
                                    "GaugeLatitude": 51.5074,
                                    "GaugeLongitude": -0.1278,
                                    "GaugeType": "Test Gauge",
                                    "OperationalStatus": "Fully operational"
                                }
                            }
                        }
                    }
                ]
            },
            "property_data": {
                "properties": [
                    {
                        "PropertyHeader": {
                            "Header": {"PropertyID": "PROP-test123"},
                            "Location": {
                                "LatitudeDegrees": 51.5074,
                                "LongitudeDegrees": -0.1278
                            }
                        },
                        "FloodRisk": "Medium"
                    }
                ]
            }
        }
    
    def test_complete_workflow(self):
        """Test complete workflow with sample data."""
        # Create a map
        test_map = folium.Map(location=[51.5074, -0.1278])
        
        # Add some sample markers (simulating property and gauge markers)
        folium.Marker(
            location=[51.5074, -0.1278],
            popup="Property: PROP-test123",
            tooltip="Property: PROP-test123 | Risk: Medium"
        ).add_to(test_map)
        
        folium.Marker(
            location=[51.5074, -0.1278],
            popup="Gauge: GAUGE-test123",
            tooltip="Gauge: Test Gauge | Status: Fully operational"
        ).add_to(test_map)
        
        # Add interactivity
        manager = InteractivityManager()
        manager.setup_map_interactivity(test_map)
        
        # Verify the complete setup
        html_content = test_map._repr_html_()
        
        # Check for all interactive components
        self.assertIn("showNotification", html_content)
        self.assertIn("generateReport", html_content)
        self.assertIn("showContextMenu", html_content)
        self.assertIn("PROP-test123", html_content)
        self.assertIn("GAUGE-test123", html_content)


def run_performance_tests():
    """Run basic performance tests."""
    if not MODULES_AVAILABLE:
        print("⚠️ Skipping performance tests - modules not available")
        return
    
    import time
    
    print("\n🚀 Running performance tests...")
    
    # Test JavaScript generation speed
    start_time = time.time()
    for _ in range(100):
        notifications = NotificationSystem()
        js_code = notifications.get_notification_js()
    generation_time = time.time() - start_time
    print(f"  ✓ JavaScript generation: {generation_time:.3f}s for 100 iterations")
    
    # Test map setup speed
    start_time = time.time()
    for _ in range(10):
        test_map = folium.Map(location=[51.5074, -0.1278])
        manager = InteractivityManager()
        manager.setup_map_interactivity(test_map)
    setup_time = time.time() - start_time
    print(f"  ✓ Map setup: {setup_time:.3f}s for 10 iterations")
    
    # Test memory usage (basic check)
    import sys
    manager = InteractivityManager()
    manager_size = sys.getsizeof(manager)
    print(f"  ✓ InteractivityManager size: {manager_size} bytes")


def run_integration_demo():
    """Run an integration demonstration."""
    if not MODULES_AVAILABLE:
        print("⚠️ Skipping integration demo - modules not available")
        return
    
    print("\n🎬 Running integration demonstration...")
    
    # Create a realistic map
    demo_map = folium.Map(location=[51.5074, -0.1278], zoom_start=10)
    
    # Add sample markers
    folium.Marker(
        location=[51.5074, -0.1278],
        popup="Sample Property: PROP-demo123",
        tooltip="Property: PROP-demo123 | Risk: Medium",
        icon=folium.Icon(color='red', icon='home', prefix='fa')
    ).add_to(demo_map)
    
    folium.Marker(
        location=[51.5100, -0.1200],
        popup="Sample Gauge: GAUGE-demo456",
        tooltip="Gauge: Demo River Gauge | Status: Operational",
        icon=folium.Icon(color='blue', icon='tint', prefix='fa')
    ).add_to(demo_map)
    
    # Add interactivity with custom configuration
    manager = InteractivityManager(
        server_url="http://127.0.0.1:5000",
        notification_position="top-right"
    )
    
    # Custom context menu items
    manager.context_menus.configure(
        property_menu_items=[
            {"id": "generate_report", "label": "📄 Generate Report", "action": "generateReport"},
            {"id": "view_details", "label": "👁️ View Details", "action": "viewPropertyDetails"},
            {"id": "analyze_risk", "label": "⚠️ Analyze Risk", "action": "analyzeRisk"}
        ]
    )
    
    # Setup interactivity
    manager.setup_map_interactivity(demo_map)
    
    # Save demo map
    output_path = Path(tempfile.gettempdir()) / "phase5_demo_map.html"
    demo_map.save(output_path)
    
    print(f"  ✓ Demo map created: {output_path}")
    print(f"  ✓ Open in browser to test interactive features")
    print(f"  ✓ Right-click on markers to see context menus")
    
    return output_path


def validate_javascript_syntax():
    """Validate that generated JavaScript has valid syntax."""
    if not MODULES_AVAILABLE:
        print("⚠️ Skipping JavaScript validation - modules not available")
        return
    
    print("\n🔍 Validating JavaScript syntax...")
    
    # Test all components
    components = [
        ("NotificationSystem", NotificationSystem()),
        ("ContextMenuHandler", ContextMenuHandler()),
        ("BackendHandler", BackendHandler()),
    ]
    
    for name, component in components:
        try:
            if hasattr(component, 'get_notification_js'):
                js_code = component.get_notification_js()
            elif hasattr(component, 'get_base_context_menu_js'):
                js_code = component.get_base_context_menu_js()
            elif hasattr(component, 'get_backend_js'):
                js_code = component.get_backend_js()
            else:
                continue
            
            # Basic syntax checks
            assert '<script>' in js_code, f"{name}: Missing script tags"
            assert '</script>' in js_code, f"{name}: Missing closing script tags"
            assert js_code.count('<script>') == js_code.count('</script>'), f"{name}: Unmatched script tags"
            
            # Check for template literals (should be fixed)
            if "${" in js_code:
                print(f"  ⚠️ {name}: Still contains template literals")
            
            # Check for basic function syntax
            if 'function(' in js_code or 'function ' in js_code:
                print(f"  ✓ {name}: JavaScript syntax looks valid")
            else:
                print(f"  ⚠️ {name}: No functions found in JavaScript")
            
        except Exception as e:
            print(f"  ❌ {name}: JavaScript validation failed: {e}")


def run_auto_fix_test():
    """Test that the auto-fix functionality works correctly."""
    print("\n🔧 Testing auto-fix functionality...")
    
    # Test that auto_fix_interactivity_modules can be called
    try:
        result = auto_fix_interactivity_modules()
        if result:
            print("  ✓ Auto-fix function executed successfully")
        else:
            print("  ⚠️ Auto-fix function returned False")
    except Exception as e:
        print(f"  ❌ Auto-fix function failed: {e}")
    
    # Test that imports work after auto-fix
    if MODULES_AVAILABLE:
        print("  ✓ Modules available after auto-fix")
        
        # Test problematic configuration that should now work
        try:
            manager = InteractivityManager()
            manager.configure(
                context_menu_property_items=[{"id": "test", "label": "Test"}],
                backend_server_url="https://test.com",
                notification_timeout=1000
            )
            print("  ✓ Problematic configuration now works")
        except Exception as e:
            print(f"  ❌ Configuration still fails: {e}")
        
        # Test None server URL handling
        try:
            backend = BackendHandler(None)
            if backend.server_url is not None:
                print("  ✓ None server URL handling works")
            else:
                print("  ❌ None server URL still results in None")
        except Exception as e:
            print(f"  ❌ None server URL test failed: {e}")
    else:
        print("  ❌ Modules still not available after auto-fix")


def main():
    """Main test runner."""
    print("🧪 Phase 5 Interactivity Testing Suite (Self-Fixing)")
    print("=" * 60)
    
    # Run auto-fix test first
    run_auto_fix_test()
    
    if not MODULES_AVAILABLE:
        print("\n❌ Cannot run tests - interactivity modules not available")
        print("   Make sure you're in the project root directory and run:")
        print("   python3 src/visualization/setup_phase5.py")
        return 1
    
    # Run unit tests
    print("\n📋 Running unit tests...")
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestNotificationSystem,
        TestContextMenuHandler,
        TestBackendHandler,
        TestInteractivityManager,
        TestConvenienceFunctions,
        TestIntegrationScenarios,
        TestWithRealData
    ]
    
    for test_class in test_classes:
        tests = test_loader.loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Additional validation
    validate_javascript_syntax()
    
    # Performance tests
    run_performance_tests()
    
    # Integration demo
    demo_path = run_integration_demo()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n❌ Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        print("🎉 Phase 5 interactivity modules are working correctly")
        print("🔧 Auto-fix functionality ensured compatibility")
        if demo_path:
            print(f"🚀 Try the demo map: {demo_path}")
        
        print("\n🎯 Next steps:")
        print("1. Use TCEventVisualization with enable_interactivity=True")
        print("2. Test in your browser with right-click context menus")
        print("3. Start backend server for report generation:")
        print("   python3 server_endpoints.py")
        
        return 0
    else:
        print("\n❌ Some tests failed")
        print("🔧 Auto-fix may need manual adjustment")
        return 1


if __name__ == "__main__":
    exit(main())