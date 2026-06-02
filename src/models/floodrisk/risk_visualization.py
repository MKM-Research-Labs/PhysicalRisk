# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Risk visualization for flood risk model.

Interactive Folium maps and static matplotlib plots for
flood depth, impact ratios, and risk level distributions.
"""

import logging
from typing import Dict, Optional

import folium

logger = logging.getLogger(__name__)
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def create_interactive_map(properties: gpd.GeoDataFrame,
                            flood_depths: np.ndarray,
                            direct_impacts: np.ndarray,
                            flood_event: Dict,
                            gauge_data: Optional[pd.DataFrame],
                            output_file: str):
    """Create interactive Folium map of flood risk."""
    # Currency label for monetary popups — driven by the active catchment.
    try:
        from config import config
        currency = config.CURRENCY
    except Exception:
        currency = "GBP"

    center_lat = properties.geometry.y.mean()
    center_lon = properties.geometry.x.mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

    for i, (_, row) in enumerate(properties.iterrows()):
        impact = direct_impacts[i]
        depth = flood_depths[i]

        if impact > 0.6:
            color, risk_label = 'red', 'High'
        elif impact > 0.3:
            color, risk_label = 'orange', 'Medium'
        elif impact > 0.1:
            color, risk_label = 'yellow', 'Low'
        else:
            color, risk_label = 'green', 'Minimal'

        popup_text = f"""
        <b>Property ID:</b> {row.get('property_id', 'Unknown')}<br>
        <b>Risk Level:</b> {risk_label}<br>
        <b>Flood Depth:</b> {depth:.2f}m<br>
        <b>Impact Ratio:</b> {impact:.2%}<br>
        <b>Property Value:</b> {currency} {row['value']:,.0f}<br>
        <b>Value at Risk:</b> {currency} {row['value'] * impact:,.0f}
        """

        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=8,
            color=color,
            fill=True,
            fillOpacity=0.7,
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(m)

    if 'center_lat' in flood_event and 'center_lon' in flood_event:
        folium.Circle(
            location=[flood_event['center_lat'], flood_event['center_lon']],
            radius=flood_event.get('radius', 10000),
            color='blue',
            fill=True,
            fillOpacity=0.2,
            popup="Flood Event Center"
        ).add_to(m)

    if gauge_data is not None:
        for _, gauge in gauge_data.iterrows():
            folium.Marker(
                location=[gauge['latitude'], gauge['longitude']],
                popup=f"Gauge: {gauge.get('gauge_id', 'Unknown')}<br>Water Level: {gauge['water_level']:.2f}m",
                icon=folium.Icon(color='blue', icon='tint')
            ).add_to(m)

    m.save(output_file)
    logger.info(f"Interactive map saved to: {output_file}")


def create_static_plots(properties: gpd.GeoDataFrame,
                          flood_depths: np.ndarray,
                          direct_impacts: np.ndarray,
                          output_file: str):
    """Create static matplotlib plots for flood risk analysis."""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

    # Flood depth histogram
    ax1.hist(flood_depths, bins=30, alpha=0.7, color='blue', edgecolor='black')
    ax1.set_xlabel('Flood Depth (m)')
    ax1.set_ylabel('Number of Properties')
    ax1.set_title('Distribution of Flood Depths')
    ax1.grid(True, alpha=0.3)

    # Impact ratio histogram
    ax2.hist(direct_impacts, bins=30, alpha=0.7, color='red', edgecolor='black')
    ax2.set_xlabel('Impact Ratio')
    ax2.set_ylabel('Number of Properties')
    ax2.set_title('Distribution of Impact Ratios')
    ax2.grid(True, alpha=0.3)

    # Scatter: depth vs impact
    scatter = ax3.scatter(flood_depths, direct_impacts,
                          c=properties['value'],
                          cmap='viridis', alpha=0.6)
    ax3.set_xlabel('Flood Depth (m)')
    ax3.set_ylabel('Impact Ratio')
    ax3.set_title('Flood Depth vs Impact Ratio')
    ax3.grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=ax3, label='Property Value (GBP)')

    # Risk level pie chart
    risk_levels = []
    for impact in direct_impacts:
        if impact > 0.6:
            risk_levels.append('High')
        elif impact > 0.3:
            risk_levels.append('Medium')
        elif impact > 0.1:
            risk_levels.append('Low')
        else:
            risk_levels.append('Minimal')

    risk_counts = pd.Series(risk_levels).value_counts()
    colors = ['red', 'orange', 'yellow', 'green']
    ax4.pie(risk_counts.values, labels=risk_counts.index, autopct='%1.1f%%',
            colors=colors[:len(risk_counts)])
    ax4.set_title('Properties by Risk Level')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Static plots saved to: {output_file}")


def visualize_risk(properties: gpd.GeoDataFrame,
                    flood_depths: np.ndarray,
                    direct_impacts: np.ndarray,
                    flood_event: Dict,
                    gauge_data: Optional[pd.DataFrame],
                    output_file_base: str = 'flood_risk'):
    """Create all risk visualization outputs (map + plots)."""
    create_interactive_map(properties, flood_depths, direct_impacts,
                           flood_event, gauge_data,
                           f"{output_file_base}.html")
    create_static_plots(properties, flood_depths, direct_impacts,
                        f"{output_file_base}.png")
