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
Backend communication handler for interactive functionality.

This module handles communication between the frontend map and backend services,
including report generation and data export functionality.
"""

from typing import Dict, Any, Optional
import folium
import json


class BackendHandler:
    """Handler for backend communication functionality."""
    
    def __init__(self, server_url="http://127.0.0.1:5001"):
        """
        Initialize the backend handler with proper None handling.
        
        Args:
            server_url: URL of the backend server
        """
        # FIXED: Explicitly handle None server_url case and use correct port
        if server_url is None:
            self.server_url = "http://127.0.0.1:5001"
            print("🔧 BackendHandler: Fixed None server_url -> default")
        else:
            self.server_url = server_url
        
        self.endpoints = {
            'property_report': '/generate_property_report',
            'gauge_report': '/generate_gauge_report',
            'export_data': '/export_data',
            'health_check': '/'
        }
    
    def get_backend_js(self) -> str:
        """
        Get JavaScript code for backend communication.
        
        Returns:
            JavaScript code as string
        """
        # Convert endpoints to JSON string properly
        endpoints_json = json.dumps(self.endpoints)
        
        js_code = f"""
        <script>
        // Backend communication functions - FIXED VERSION
        
        // Configuration
        const BACKEND_CONFIG = {{
            serverUrl: '{self.server_url}',
            endpoints: {endpoints_json},
            timeout: 30000  // 30 seconds
        }};
        
        console.log('🔧 Backend config loaded:', BACKEND_CONFIG);
        
        // Show loading notification
        function showNotification(message, type = 'info') {{
            console.log('📢 Notification:', message, '(' + type + ')');
            
            // Remove any existing notifications first
            const existingNotifications = document.querySelectorAll('.map-notification');
            existingNotifications.forEach(notif => notif.remove());
            
            const notification = document.createElement('div');
            notification.className = 'map-notification';
            notification.style.cssText = 
                'position: fixed;' +
                'top: 20px;' +
                'right: 20px;' +
                'padding: 12px 20px;' +
                'background: ' + (type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3') + ';' +
                'color: white;' +
                'border-radius: 4px;' +
                'z-index: 10000;' +
                'font-family: Arial, sans-serif;' +
                'font-size: 14px;' +
                'box-shadow: 0 2px 10px rgba(0,0,0,0.2);' +
                'max-width: 300px;' +
                'word-wrap: break-word;' +
                'line-height: 1.4;' +
                'white-space: pre-line;';
            notification.textContent = message;
            document.body.appendChild(notification);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {{
                if (notification.parentNode) {{
                    notification.parentNode.removeChild(notification);
                }}
            }}, 5000);
            
            // Allow manual close on click
            notification.addEventListener('click', () => {{
                if (notification.parentNode) {{
                    notification.parentNode.removeChild(notification);
                }}
            }});
        }}
        
        // Generic API call function - FIXED CORS and error handling
        async function callBackendAPI(endpoint, data, successMessage) {{
            console.log('🔌 API Call:', endpoint, 'Data:', data);
            
            try {{
                showNotification('Processing request...', 'info');
                
                const url = BACKEND_CONFIG.serverUrl + endpoint;
                console.log('🌐 Fetching:', url);
                
                const response = await fetch(url, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }},
                    body: JSON.stringify(data),
                    mode: 'cors'
                }});
                
                console.log('📡 Response status:', response.status);
                
                if (!response.ok) {{
                    const errorText = await response.text();
                    throw new Error(`HTTP ${{response.status}}: ${{errorText}}`);
                }}
                
                const result = await response.json();
                console.log('✅ API Response:', result);
                
                if (result.status === 'success') {{
                    showNotification(
                        '✅ ' + successMessage + '\\\\n' + (result.message || 'Operation completed!'), 
                        'success'
                    );
                    
                    // If file path is provided, show it
                    if (result.file_path) {{
                        console.log('📄 Report saved to:', result.file_path);
                        setTimeout(() => {{
                            showNotification('📄 Report saved to:\\n' + result.file_path, 'info');
                        }}, 2000);
                    }}
                    
                    return result;
                }} else {{
                    const errorMsg = result.message || 'Unknown error occurred';
                    showNotification('❌ Error: ' + errorMsg, 'error');
                    console.error('❌ API call failed:', result);
                    return null;
                }}
            }} catch (error) {{
                console.error('🚨 Backend API error:', error);
                
                let errorMessage = '🚫 Request failed';
                
                if (error.name === 'AbortError') {{
                    errorMessage = '⏱️ Request timed out. Please try again.';
                }} else if (error instanceof TypeError && error.message.includes('fetch')) {{
                    errorMessage = '🔌 Cannot connect to server.\\n\\nPlease check:\\n1. Server is running on ' + BACKEND_CONFIG.serverUrl + '\\n2. CORS is enabled\\n3. Network connectivity';
                }} else if (error.message.includes('CORS')) {{
                    errorMessage = '🚫 CORS Error: Server needs CORS configuration';
                }} else if (error.message.includes('HTTP 500')) {{
                    errorMessage = '🚫 Server Error: Internal server error occurred';
                }} else if (error.message.includes('HTTP 404')) {{
                    errorMessage = '🚫 Not Found: Check if the item exists';
                }} else {{
                    errorMessage = '🚫 Error: ' + error.message;
                }}
                
                showNotification(errorMessage, 'error');
                return null;
            }}
        }}
        
        // Generate PDF report function (Properties) - FIXED
        async function generateReport(propertyId) {{
            console.log('📊 generateReport called with:', propertyId);
            
            if (!propertyId) {{
                console.error('❌ Property ID not provided');
                showNotification('❌ Property ID not found', 'error');
                return;
            }}
            
            console.log('📊 Generating report for property:', propertyId);
            
            const result = await callBackendAPI(
                BACKEND_CONFIG.endpoints.property_report,
                {{ propertyId: propertyId }},
                'Property report generated!'
            );
            
            return result;
        }}
        
        // Generate Gauge Report function - FIXED
        async function generateGaugeReport(gaugeId) {{
            console.log('🌊 generateGaugeReport called with:', gaugeId);
            
            if (!gaugeId) {{
                console.error('❌ Gauge ID not provided');
                showNotification('❌ Gauge ID not found', 'error');
                return;
            }}
            
            console.log('🌊 Generating gauge report for:', gaugeId);
            
            const result = await callBackendAPI(
                BACKEND_CONFIG.endpoints.gauge_report,
                {{ gaugeId: gaugeId }},
                'Gauge report generated!'
            );
            
            return result;
        }}
        
        // Export Gauge Data function - FIXED
        async function exportGaugeData(gaugeId) {{
            console.log('📤 exportGaugeData called with:', gaugeId);
            
            if (!gaugeId) {{
                console.error('❌ Gauge ID not provided');
                showNotification('❌ Gauge ID not found', 'error');
                return;
            }}
            
            console.log('📤 Exporting data for gauge:', gaugeId);
            
            const result = await callBackendAPI(
                BACKEND_CONFIG.endpoints.export_data,
                {{ gaugeId: gaugeId, format: 'csv' }},
                'Gauge data exported!'
            );
            
            return result;
        }}
        
        // View Gauge Time Series function - FIXED
        function viewGaugeTimeSeries(gaugeId) {{
            console.log('📈 viewGaugeTimeSeries called with:', gaugeId);
            
            if (!gaugeId) {{
                console.error('❌ Gauge ID not provided');
                showNotification('❌ Gauge ID not found', 'error');
                return;
            }}
            
            console.log('📈 Viewing time series for gauge:', gaugeId);
            showNotification('📈 Time series view for ' + gaugeId + '\\nFeature coming soon!', 'info');
            
            // In a full implementation, this could open a new window or modal
            // window.open('/timeseries/' + gaugeId, '_blank');
        }}
        
        // View property details function - FIXED
        function viewPropertyDetails(propertyId) {{
            console.log('🏠 viewPropertyDetails called with:', propertyId);
            
            if (!propertyId) {{
                console.error('❌ Property ID not provided');
                showNotification('❌ Property ID not found', 'error');
                return;
            }}
            
            console.log('🏠 Viewing details for property:', propertyId);
            
            // Get the map instance
            const mapInstance = getMapInstance();
            if (!mapInstance) {{
                console.error('❌ Map instance not found');
                showNotification('❌ Map not available', 'error');
                return;
            }}
            
            // Find and open the popup for this property
            let found = false;
            mapInstance.eachLayer(function(layer) {{
                if (layer instanceof L.Marker) {{
                    // Check if this marker has the property ID
                    if (layer._markerId === propertyId) {{
                        layer.openPopup();
                        found = true;
                        return;
                    }}
                    
                    // Alternative: check tooltip content
                    if (layer.getTooltip && layer.getTooltip()) {{
                        const tooltip = layer.getTooltip();
                        if (tooltip && tooltip.getContent && 
                            tooltip.getContent().includes('Property: ' + propertyId)) {{
                            layer.openPopup();
                            found = true;
                            return;
                        }}
                    }}
                    
                    // Alternative: check popup content
                    if (layer.getPopup && layer.getPopup()) {{
                        const popup = layer.getPopup();
                        if (popup && popup.getContent && 
                            popup.getContent().includes(propertyId)) {{
                            layer.openPopup();
                            found = true;
                            return;
                        }}
                    }}
                }}
            }});
            
            if (!found) {{
                console.log('⚠️ Property marker not found, showing generic details');
                showNotification('🏠 Showing details for property: ' + propertyId + '\\n\\nDetailed popup not found, but report generation is available.', 'info');
            }} else {{
                console.log('✅ Found and opened popup for property');
                showNotification('🏠 Showing details for property: ' + propertyId, 'success');
            }}
        }}
        
        // Health check function - FIXED
        async function checkBackendHealth() {{
            console.log('🏥 Checking backend health...');
            
            try {{
                const response = await fetch(BACKEND_CONFIG.serverUrl + BACKEND_CONFIG.endpoints.health_check, {{
                    method: 'GET',
                    mode: 'cors',
                    headers: {{
                        'Accept': 'application/json'
                    }}
                }});
                
                if (response.ok) {{
                    const result = await response.json();
                    console.log('✅ Backend server is healthy:', result);
                    return true;
                }} else {{
                    console.log('⚠️ Backend server responded with error:', response.status);
                    return false;
                }}
            }} catch (error) {{
                console.log('❌ Backend server is not accessible:', error.message);
                return false;
            }}
        }}
        
        // Helper function to get map instance - IMPROVED
        function getMapInstance() {{
            // Try to find the map instance in the global scope
            const mapKeys = Object.keys(window).filter(key => key.startsWith('map_'));
            if (mapKeys.length > 0) {{
                console.log('🗺️ Found map instance:', mapKeys[0]);
                return window[mapKeys[0]];
            }}
            
            // Fallback: try common map variable names
            if (typeof map !== 'undefined') {{
                console.log('🗺️ Using global map variable');
                return map;
            }}
            if (typeof mapInstance !== 'undefined') {{
                console.log('🗺️ Using global mapInstance variable');
                return mapInstance;
            }}
            
            console.log('❌ No map instance found in global scope');
            return null;
        }}
        
        // Initialize backend communication - IMPROVED
        function initializeBackendHandler() {{
            console.log('🚀 Backend handler initializing...');
            console.log('🌐 Backend server: ' + BACKEND_CONFIG.serverUrl);
            console.log('🔗 Available endpoints:', Object.keys(BACKEND_CONFIG.endpoints));
            
            // Verify functions are properly defined
            const requiredFunctions = [
                'generateReport', 'generateGaugeReport', 'exportGaugeData', 
                'viewGaugeTimeSeries', 'viewPropertyDetails', 'checkBackendHealth'
            ];
            
            const missingFunctions = requiredFunctions.filter(funcName => typeof window[funcName] === 'undefined');
            
            if (missingFunctions.length > 0) {{
                console.error('❌ Missing functions:', missingFunctions);
            }} else {{
                console.log('✅ All required functions are defined');
            }}
            
            // Test basic functionality
            try {{
                const testMap = getMapInstance();
                if (testMap) {{
                    console.log('✅ Map instance accessible');
                }} else {{
                    console.log('⚠️ Map instance not yet available (may initialize later)');
                }}
            }} catch (error) {{
                console.log('⚠️ Error testing map access:', error);
            }}
            
            // Optional: Check backend health on initialization
            setTimeout(() => {{
                checkBackendHealth().then(healthy => {{
                    if (healthy) {{
                        console.log('✅ Backend health check passed');
                    }} else {{
                        console.log('⚠️ Backend health check failed');
                    }}
                }});
            }}, 1000);
            
            console.log('✅ Backend handler initialization complete');
        }}
        
        // Make functions globally available - CRITICAL FIX
        window.generateReport = generateReport;
        window.generateGaugeReport = generateGaugeReport;
        window.exportGaugeData = exportGaugeData;
        window.viewGaugeTimeSeries = viewGaugeTimeSeries;
        window.viewPropertyDetails = viewPropertyDetails;
        window.checkBackendHealth = checkBackendHealth;
        window.showNotification = showNotification;
        window.getMapInstance = getMapInstance;
        
        console.log('🌐 Functions made globally available');
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', initializeBackendHandler);
        }} else {{
            initializeBackendHandler();
        }}
        </script>
        """
        
        return js_code
    
    def add_to_map(self, folium_map: folium.Map) -> None:
        """
        Add backend communication functionality to a Folium map.
        
        Args:
            folium_map: The Folium map to add backend functionality to
        """
        # Add the backend JavaScript
        backend_js = self.get_backend_js()
        folium_map.get_root().html.add_child(folium.Element(backend_js))
        
        print("✅ Backend communication functionality added to map")
        print(f"🌐 Server URL: {self.server_url}")
        print(f"🔗 Endpoints: {list(self.endpoints.keys())}")
    
    def configure(self, server_url: Optional[str] = None, 
                 endpoints: Optional[Dict[str, str]] = None) -> None:
        """
        Configure backend settings.
        
        Args:
            server_url: Backend server URL
            endpoints: Custom endpoint mappings
        """
        if server_url:
            self.server_url = server_url
        
        if endpoints:
            self.endpoints.update(endpoints)
        
        print(f"✅ Backend handler configured for server: {self.server_url}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about backend configuration.
        
        Returns:
            Dictionary with backend statistics
        """
        return {
            'server_url': self.server_url,
            'total_endpoints': len(self.endpoints),
            'endpoints': list(self.endpoints.keys())
        }