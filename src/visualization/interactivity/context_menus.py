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
Context menu functionality for interactive map markers.

This module handles the creation and management of right-click context menus
for property and gauge markers, extracted from the original visualization.py.
"""

from typing import Dict, Any, Optional, List
import folium
from pathlib import Path


class ContextMenuHandler:
    """Handler for context menu functionality on map markers."""
    
    def __init__(self):
        """Initialize the context menu handler."""
        self.property_menu_items = [
            {"id": "generate_report", "label": "📄 Generate PDF Report", "action": "generateReport"},
            {"id": "view_details", "label": "👁️ View Details", "action": "viewPropertyDetails"}
        ]
        
        self.gauge_menu_items = [
            {"id": "generate_gauge_report", "label": "📊 Generate Gauge Report", "action": "generateGaugeReport"},
            {"id": "view_time_series", "label": "📈 View Time Series", "action": "viewGaugeTimeSeries"},
            {"id": "export_data", "label": "💾 Export Data", "action": "exportGaugeData"}
        ]
    
    def get_property_context_menu_js(self) -> str:
        """
        Get JavaScript code for property context menus.
        
        Returns:
            JavaScript code as string
        """
        return self._load_js_template("property_context_menu.js")
    
    def get_gauge_context_menu_js(self) -> str:
        """
        Get JavaScript code for gauge context menus.
        
        Returns:
            JavaScript code as string
        """
        return self._load_js_template("gauge_context_menu.js")
    
    def get_base_context_menu_js(self) -> str:
        """
        Get base JavaScript code for context menu functionality.
        
        Returns:
            JavaScript code as string
        """
        js_code = f"""
        <script>
        // Global variables
        let currentPropertyId = null;
        let currentGaugeId = null;
        let mapInstance = null;
        
        // Store reference to the map when it's ready
        document.addEventListener('DOMContentLoaded', function() {{
            // Wait for the map to be fully loaded
            setTimeout(function() {{
                // Get the map instance from the global window object
                if (typeof window[Object.keys(window).find(key => key.startsWith('map_'))] !== 'undefined') {{
                    mapInstance = window[Object.keys(window).find(key => key.startsWith('map_'))];
                    console.log('Map instance found:', mapInstance);
                    initializeContextMenus();
                }} else {{
                    console.log('Map instance not found, retrying...');
                    setTimeout(arguments.callee, 500);
                }}
            }}, 1000);
        }});
        
        // Create context menu element
        function createContextMenu(menuId, menuItems) {{
            // Remove existing menu if it exists
            const existingMenu = document.getElementById(menuId);
            if (existingMenu) {{
                existingMenu.remove();
            }}
            
            const menu = document.createElement('div');
            menu.id = menuId;
            menu.style.cssText = 
                'position: absolute;' +
                'background: white;' +
                'border: 1px solid #ccc;' +
                'border-radius: 4px;' +
                'padding: 8px 0;' +
                'box-shadow: 0 2px 10px rgba(0,0,0,0.2);' +
                'z-index: 1000;' +
                'display: none;' +
                'font-family: Arial, sans-serif;' +
                'font-size: 14px;' +
                'min-width: 150px;';
            
            menuItems.forEach(item => {{
                const menuItem = document.createElement('div');
                menuItem.innerHTML = item.label;
                menuItem.style.cssText = 
                    'padding: 8px 16px;' +
                    'cursor: pointer;' +
                    'border-bottom: 1px solid #eee;';
                menuItem.onmouseover = () => menuItem.style.backgroundColor = '#f0f0f0';
                menuItem.onmouseout = () => menuItem.style.backgroundColor = 'white';
                menuItem.onclick = () => {{
                    if (item.action && typeof window[item.action] === 'function') {{
                        if (menuId.includes('property')) {{
                            window[item.action](currentPropertyId);
                        }} else if (menuId.includes('gauge')) {{
                            window[item.action](currentGaugeId);
                        }}
                    }}
                    hideContextMenu(menuId);
                }};
                
                menu.appendChild(menuItem);
            }});
            
            document.body.appendChild(menu);
            return menu;
        }}
        
        // Show context menu
        function showContextMenu(e, itemId, menuType) {{
            e.preventDefault();
            e.stopPropagation();
            
            if (menuType === 'property') {{
                currentPropertyId = itemId;
                showPropertyContextMenu(e);
            }} else if (menuType === 'gauge') {{
                currentGaugeId = itemId;
                showGaugeContextMenu(e);
            }}
            
            console.log('Context menu shown for ' + menuType + ': ' + itemId);
        }}
        
        // Show property context menu
        function showPropertyContextMenu(e) {{
            const menuItems = {self.property_menu_items};
            let menu = document.getElementById('property-context-menu');
            if (!menu) {{
                menu = createContextMenu('property-context-menu', menuItems);
            }}
            
            menu.style.left = e.pageX + 'px';
            menu.style.top = e.pageY + 'px';
            menu.style.display = 'block';
        }}
        
        // Show gauge context menu
        function showGaugeContextMenu(e) {{
            const menuItems = {self.gauge_menu_items};
            let menu = document.getElementById('gauge-context-menu');
            if (!menu) {{
                menu = createContextMenu('gauge-context-menu', menuItems);
            }}
            
            menu.style.left = e.pageX + 'px';
            menu.style.top = e.pageY + 'px';
            menu.style.display = 'block';
        }}
        
        // Hide context menu
        function hideContextMenu(menuId) {{
            const menu = document.getElementById(menuId);
            if (menu) {{
                menu.style.display = 'none';
            }}
        }}
        
        // Hide all context menus when clicking elsewhere
        document.addEventListener('click', function() {{
            hideContextMenu('property-context-menu');
            hideContextMenu('gauge-context-menu');
        }});
        
        // Function to extract property ID from marker tooltip
        function extractPropertyIdFromTooltip(tooltipText) {{
            if (!tooltipText) return null;
            
            // Look for "Property: XXXXX" pattern
            const match = tooltipText.match(/Property:\\s*([^|]+)/);
            if (match) {{
                return match[1].trim();
            }}
            return null;
        }}
        
        // Function to extract gauge ID from marker tooltip
        function extractGaugeIdFromTooltip(tooltipText) {{
            if (!tooltipText) return null;
            
            // FIRST: Look for specific GAUGE-XXXXX pattern (most precise)
            let match = tooltipText.match(/(GAUGE-[a-f0-9]+)/);
            if (match) {{
                return match[1].trim();
            }}
            
            // FALLBACK: Look for "Gauge: XXXXX" pattern (less precise)
            match = tooltipText.match(/Gauge:\s*([^|]+)/);
            if (match) {{
                return match[1].trim();  
            }}
            
            return null;
        }}
        
        // Function to extract ID from popup content
        function extractIdFromPopup(popupContent) {{
            if (!popupContent) return null;
            
            // Convert to string if it's not already
            let contentString = '';
            if (typeof popupContent === 'string') {{
                contentString = popupContent;
            }} else if (popupContent && typeof popupContent.toString === 'function') {{
                contentString = popupContent.toString();
            }} else if (popupContent && popupContent.innerHTML) {{
                contentString = popupContent.innerHTML;
            }} else if (popupContent && popupContent.textContent) {{
                contentString = popupContent.textContent;
            }} else {{
                console.log('Could not convert popup content to string:', typeof popupContent);
                return null;
            }}
            
            // Look for "ID: XXXXX" pattern in the popup HTML
            const match = contentString.match(/ID:\\s*([^<\\r\\n]+)/);
            if (match) {{
                return match[1].trim();
            }}
            return null;
        }}
        
        // Initialize context menu functionality
        function initializeContextMenus() {{
            if (!mapInstance) {{
                console.log('Map instance not available for context menu initialization');
                return;
            }}
            
            console.log('Initializing context menus...');
            
            // Function to add context menu to markers
            function addContextMenuToMarkers() {{
                let propertyMarkerCount = 0;
                let gaugeMarkerCount = 0;
                
                mapInstance.eachLayer(function(layer) {{
                    if (layer instanceof L.Marker) {{
                        // Skip if already has context menu listener
                        if (layer._hasContextMenu) return;
                        
                        // Try to determine marker type and extract ID
                        let markerId = null;
                        let markerType = null;
                        
                        // Method 1: From tooltip
                        if (layer.getTooltip && layer.getTooltip()) {{
                            const tooltipContent = layer.getTooltip().getContent();
                            
                            // Check for property marker
                            const propertyId = extractPropertyIdFromTooltip(tooltipContent);
                            if (propertyId) {{
                                markerId = propertyId;
                                markerType = 'property';
                            }} else {{
                                // Check for gauge marker
                                const gaugeId = extractGaugeIdFromTooltip(tooltipContent);
                                if (gaugeId) {{
                                    markerId = gaugeId;
                                    markerType = 'gauge';
                                }}
                            }}
                        }}
                        
                        // Method 2: From popup content
                        if (!markerId && layer.getPopup && layer.getPopup()) {{
                            const popupContent = layer.getPopup().getContent();
                            const extractedId = extractIdFromPopup(popupContent);
                            
                            if (extractedId) {{
                                if (extractedId.startsWith('PROP-')) {{
                                    markerId = extractedId;
                                    markerType = 'property';
                                }} else if (extractedId.startsWith('GAUGE-')) {{
                                    markerId = extractedId;
                                    markerType = 'gauge';
                                }}
                            }}
                        }}
                        
                        // Add context menu if we identified the marker
                        if (markerId && markerType) {{
                            // Add right-click event listener
                            layer.on('contextmenu', function(e) {{
                                showContextMenu(e.originalEvent, markerId, markerType);
                            }});
                            
                            // Mark as having context menu
                            layer._hasContextMenu = true;
                            layer._markerId = markerId;
                            layer._markerType = markerType;
                            
                            if (markerType === 'property') {{
                                propertyMarkerCount++;
                            }} else if (markerType === 'gauge') {{
                                gaugeMarkerCount++;
                            }}
                            
                            console.log('Added context menu to ' + markerType + ': ' + markerId);
                        }}
                    }}
                }});
                
                console.log('Added context menus to ' + propertyMarkerCount + ' property markers and ' + gaugeMarkerCount + ' gauge markers');
            }}
            
            // Add context menus to existing markers
            addContextMenuToMarkers();
            
            // Re-add context menus when new layers are added
            mapInstance.on('layeradd', function(e) {{
                setTimeout(function() {{
                    addContextMenuToMarkers();
                }}, 100);
            }});
            
            console.log('Context menu initialization complete');
        }}
        </script>
        """
        
        return js_code
    
    def _load_js_template(self, template_name: str) -> str:
        """
        Load JavaScript template from file.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            JavaScript code as string
        """
        # For now, return empty string as templates would be in separate files
        # In a full implementation, these would be loaded from template files
        return ""
    
    def add_to_map(self, folium_map: folium.Map) -> None:
        """
        Add context menu functionality to a Folium map.
        
        Args:
            folium_map: The Folium map to add context menus to
        """
        # Add the base context menu JavaScript
        base_js = self.get_base_context_menu_js()
        folium_map.get_root().html.add_child(folium.Element(base_js))
        
        print("✅ Context menu functionality added to map")
    
    def configure(self, property_menu_items: Optional[List[Dict[str, str]]] = None,
                 gauge_menu_items: Optional[List[Dict[str, str]]] = None) -> None:
        """
        Configure context menu items.
        
        Args:
            property_menu_items: Custom property menu items
            gauge_menu_items: Custom gauge menu items
        """
        if property_menu_items:
            self.property_menu_items = property_menu_items
        
        if gauge_menu_items:
            self.gauge_menu_items = gauge_menu_items
        
        print("✅ Context menu items configured")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about context menu configuration.
        
        Returns:
            Dictionary with context menu statistics
        """
        return {
            'property_menu_items': len(self.property_menu_items),
            'gauge_menu_items': len(self.gauge_menu_items),
            'total_menu_items': len(self.property_menu_items) + len(self.gauge_menu_items)
        }