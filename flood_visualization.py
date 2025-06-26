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
Flood Risk Visualization Tool
Creates interactive visualizations from flood_risk_report.json
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium import plugins
import sys
from pathlib import Path

# Setup project root and paths (same pattern as run_portfolio)
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def debug_paths():
    """Debug function to show current working directory and paths."""
    print("🔍 PATH DEBUG INFORMATION")
    print("=" * 50)
    print(f"Script location: {Path(__file__).resolve()}")
    print(f"Project root: {project_root}")
    print(f"Current working directory: {Path.cwd()}")
    print(f"Expected input file: {project_root / 'input' / 'flood_risk_report.json'}")
    print(f"Expected output dir: {project_root / 'output'}")
    print()

def load_flood_data(json_file):
    """Load and validate property portfolio data."""
    try:
        print(f"📖 Attempting to load: {json_file}")
        print(f"📖 File exists: {json_file.exists()}")
        if json_file.exists():
            print(f"📖 File size: {json_file.stat().st_size} bytes")
        
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Look for properties in the correct structure
        if 'properties' not in data:
            raise ValueError("Missing 'properties' in JSON file")
        
        print(f"✅ Successfully loaded data with {len(data['properties'])} properties")
        return data
    except Exception as e:
        print(f"❌ Error loading JSON file: {e}")
        return None

def create_property_dataframe(property_data):
    """Convert property data to pandas DataFrame."""
    properties = property_data['properties']
    
    # Extract the nested property information into a flat structure
    flattened_properties = []
    
    for prop in properties:
        property_header = prop.get('PropertyHeader', {})
        header = property_header.get('Header', {})
        location = property_header.get('Location', {})
        valuation = property_header.get('Valuation', {})
        risk_assessment = property_header.get('RiskAssessment', {})
        
        flat_prop = {
            'property_id': header.get('PropertyID', 'Unknown'),
            'latitude': location.get('LatitudeDegrees', 0),
            'longitude': location.get('LongitudeDegrees', 0),
            'elevation': risk_assessment.get('elevation', 0),
            'property_value': valuation.get('PropertyValue', 0),
            'flood_zone': risk_assessment.get('EAFloodZone', 'Unknown'),
            'flood_risk': risk_assessment.get('OverallFloodRisk', 'Unknown'),
            'postcode': location.get('Postcode', 'Unknown'),
            'address': f"{location.get('BuildingNumber', '')} {location.get('StreetName', '')}".strip(),
            'town': location.get('TownCity', 'Unknown')
        }
        
        # Simulate flood depth and risk levels based on flood zone and elevation
        if flat_prop['flood_zone'] == 'Zone 3a':
            # High flood risk zone
            if flat_prop['elevation'] < 15:
                flat_prop['flood_depth'] = max(0, 2.5 - (flat_prop['elevation'] - 10) * 0.3)
                flat_prop['risk_level'] = 'High'
            elif flat_prop['elevation'] < 25:
                flat_prop['flood_depth'] = max(0, 1.5 - (flat_prop['elevation'] - 15) * 0.15)
                flat_prop['risk_level'] = 'Medium'
            else:
                flat_prop['flood_depth'] = 0
                flat_prop['risk_level'] = 'Minimal'
        elif flat_prop['flood_zone'] == 'Zone 2':
            # Medium flood risk zone
            if flat_prop['elevation'] < 20:
                flat_prop['flood_depth'] = max(0, 1.0 - (flat_prop['elevation'] - 15) * 0.2)
                flat_prop['risk_level'] = 'Medium'
            else:
                flat_prop['flood_depth'] = 0
                flat_prop['risk_level'] = 'Low'
        else:
            # Zone 1 or unknown - low risk
            flat_prop['flood_depth'] = 0
            flat_prop['risk_level'] = 'Minimal'
        
        # Calculate value at risk based on flood depth
        if flat_prop['flood_depth'] > 0:
            damage_ratio = min(0.8, flat_prop['flood_depth'] * 0.3)  # Max 80% damage
            flat_prop['value_at_risk'] = flat_prop['property_value'] * damage_ratio
            flat_prop['impact_ratio'] = damage_ratio
        else:
            flat_prop['value_at_risk'] = 0
            flat_prop['impact_ratio'] = 0
        
        flattened_properties.append(flat_prop)
    
    df = pd.DataFrame(flattened_properties)
    
    print(f"📊 DataFrame created with {len(df)} rows and columns: {list(df.columns)}")
    
    # Clean and validate data
    df['flood_depth'] = pd.to_numeric(df['flood_depth'], errors='coerce').fillna(0)
    df['property_value'] = pd.to_numeric(df['property_value'], errors='coerce').fillna(0)
    df['value_at_risk'] = pd.to_numeric(df['value_at_risk'], errors='coerce').fillna(0)
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    
    # Drop rows with invalid coordinates
    original_count = len(df)
    df = df.dropna(subset=['latitude', 'longitude'])
    
    print(f"📊 After cleaning: {len(df)} properties (removed {original_count - len(df)} with invalid coordinates)")
    
    # Print summary statistics
    flooded_count = len(df[df['flood_depth'] > 0])
    total_value = df['property_value'].sum()
    total_value_at_risk = df['value_at_risk'].sum()
    
    print(f"📊 Summary: {flooded_count} properties with flood risk, £{total_value/1000000:.1f}M total value, £{total_value_at_risk/1000000:.1f}M at risk")
    
    return df

def get_marker_color(risk_level):
    """Get color for risk level."""
    colors = {
        'High': 'red',
        'Medium': 'orange', 
        'Low': 'yellow',
        'Minimal': 'green'
    }
    return colors.get(risk_level, 'gray')

def create_interactive_map(df, output_path):
    """Create interactive Folium map."""
    print(f"🗺️ Creating map with {len(df)} properties...")
    
    # Calculate map center
    center_lat = df['latitude'].mean()
    center_lng = df['longitude'].mean()
    
    print(f"🗺️ Map center: {center_lat:.4f}, {center_lng:.4f}")
    
    # Create base map
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=11,
        tiles='OpenStreetMap'
    )
    
    # Add marker clusters for better performance
    marker_cluster = plugins.MarkerCluster().add_to(m)
    
    # Add property markers
    marker_count = 0
    for idx, property_data in df.iterrows():
        # Calculate marker size based on property value
        value = property_data['property_value']
        if value > 2000000:
            radius = 12
        elif value > 1000000:
            radius = 10
        elif value > 500000:
            radius = 8
        else:
            radius = 6
        
        # Create popup content
        popup_html = f"""
        <div style="font-size: 14px; min-width: 200px;">
            <h4 style="margin: 0 0 10px 0; color: #333;">{property_data['property_id']}</h4>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td><b>Risk Level:</b></td><td style="color: {get_marker_color(property_data['risk_level'])};">{property_data['risk_level']}</td></tr>
                <tr><td><b>Flood Depth:</b></td><td>{property_data['flood_depth']:.2f}m</td></tr>
                <tr><td><b>Elevation:</b></td><td>{property_data.get('elevation', 'N/A')}m</td></tr>
                <tr><td><b>Property Value:</b></td><td>£{property_data['property_value']:,.0f}</td></tr>
                <tr><td><b>Value at Risk:</b></td><td>£{property_data['value_at_risk']:,.0f}</td></tr>
                <tr><td><b>Impact Ratio:</b></td><td>{property_data.get('impact_ratio', 0)*100:.1f}%</td></tr>
            </table>
        </div>
        """
        
        # Add circle marker
        folium.CircleMarker(
            location=[property_data['latitude'], property_data['longitude']],
            radius=radius,
            popup=folium.Popup(popup_html, max_width=300),
            color='white',
            weight=2,
            fillColor=get_marker_color(property_data['risk_level']),
            fillOpacity=0.8,
            tooltip=f"{property_data['property_id']} - {property_data['risk_level']} Risk"
        ).add_to(marker_cluster)
        
        marker_count += 1
    
    print(f"🗺️ Added {marker_count} markers to map")
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 140px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px;
                ">
    <h4 style="margin-top:0;">Risk Level Legend</h4>
    <p><span style="color:red;">●</span> High Risk (>1.5m)</p>
    <p><span style="color:orange;">●</span> Medium Risk (0.5-1.5m)</p>
    <p><span style="color:gold;">●</span> Low Risk (0.1-0.5m)</p>
    <p><span style="color:green;">●</span> Minimal Risk (<0.1m)</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Save map
    map_file = output_path / 'flood_risk_map.html'
    m.save(str(map_file))
    print(f"✅ Interactive map saved: {map_file}")
    
    return m

def create_analysis_charts(df, property_data, output_path):
    """Create analysis charts and save as images."""
    print("📈 Creating analysis charts...")
    
    # Set style
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Flood Risk Portfolio Analysis', fontsize=20, fontweight='bold')
    
    # 1. Risk Level Distribution
    risk_counts = df['risk_level'].value_counts()
    colors = [get_marker_color(level) for level in risk_counts.index]
    
    axes[0, 0].pie(risk_counts.values, labels=risk_counts.index, autopct='%1.1f%%',
                   colors=colors, startangle=90)
    axes[0, 0].set_title('Risk Level Distribution', fontsize=14, fontweight='bold')
    
    # 2. Flood Depth Distribution
    flood_depths = df[df['flood_depth'] > 0]['flood_depth']
    if len(flood_depths) > 0:
        axes[0, 1].hist(flood_depths, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0, 1].set_xlabel('Flood Depth (m)')
        axes[0, 1].set_ylabel('Number of Properties')
        axes[0, 1].set_title('Flood Depth Distribution (Flooded Properties Only)', 
                            fontsize=14, fontweight='bold')
        axes[0, 1].axvline(flood_depths.mean(), color='red', linestyle='--', 
                          label=f'Mean: {flood_depths.mean():.2f}m')
        axes[0, 1].legend()
    else:
        axes[0, 1].text(0.5, 0.5, 'No flooded properties', 
                       ha='center', va='center', transform=axes[0, 1].transAxes)
        axes[0, 1].set_title('Flood Depth Distribution', fontsize=14, fontweight='bold')
    
    # 3. Property Value vs Flood Depth
    scatter_colors = [get_marker_color(level) for level in df['risk_level']]
    axes[1, 0].scatter(df['property_value']/1000000, df['flood_depth'], 
                      c=scatter_colors, alpha=0.6, s=50)
    axes[1, 0].set_xlabel('Property Value (£M)')
    axes[1, 0].set_ylabel('Flood Depth (m)')
    axes[1, 0].set_title('Property Value vs Flood Depth', fontsize=14, fontweight='bold')
    
    # 4. Value at Risk by Risk Level
    value_at_risk = df.groupby('risk_level')['value_at_risk'].sum() / 1000000
    if len(value_at_risk) > 0:
        bars = axes[1, 1].bar(value_at_risk.index, value_at_risk.values, 
                             color=[get_marker_color(level) for level in value_at_risk.index])
        axes[1, 1].set_xlabel('Risk Level')
        axes[1, 1].set_ylabel('Value at Risk (£M)')
        axes[1, 1].set_title('Value at Risk by Risk Level', fontsize=14, fontweight='bold')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            axes[1, 1].text(bar.get_x() + bar.get_width()/2., height,
                           f'£{height:.1f}M', ha='center', va='bottom')
    
    plt.tight_layout()
    
    # Save charts
    chart_file = output_path / 'flood_risk_analysis.png'
    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
    print(f"✅ Analysis charts saved: {chart_file}")
    
    plt.show()

def generate_summary_report(df, property_data, output_path):
    """Generate text summary report."""
    print("📝 Generating summary report...")
    
    # Calculate summary statistics
    total_properties = len(df)
    properties_at_risk = len(df[df['flood_depth'] > 0])
    percentage_at_risk = (properties_at_risk / total_properties) * 100 if total_properties > 0 else 0
    total_value = df['property_value'].sum()
    value_at_risk = df['value_at_risk'].sum()
    percentage_value_at_risk = (value_at_risk / total_value) * 100 if total_value > 0 else 0
    avg_flood_depth = df['flood_depth'].mean()
    max_flood_depth = df['flood_depth'].max()
    avg_impact_ratio = df['impact_ratio'].mean()
    
    report_lines = [
        "FLOOD RISK PORTFOLIO ANALYSIS SUMMARY",
        "=" * 50,
        "",
        f"Report Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total Properties Analyzed: {total_properties:,}",
        "",
        "PORTFOLIO OVERVIEW:",
        f"• Total Portfolio Value: £{total_value/1000000:.1f}M",
        f"• Properties at Risk: {properties_at_risk:,} ({percentage_at_risk:.1f}%)",
        f"• Total Value at Risk: £{value_at_risk/1000000:.1f}M ({percentage_value_at_risk:.1f}%)",
        "",
        "FLOOD DEPTH STATISTICS:",
        f"• Average Flood Depth: {avg_flood_depth:.2f}m",
        f"• Maximum Flood Depth: {max_flood_depth:.2f}m",
        f"• Average Impact Ratio: {avg_impact_ratio*100:.1f}%",
        "",
        "RISK LEVEL BREAKDOWN:",
    ]
    
    # Add risk level counts
    risk_counts = df['risk_level'].value_counts()
    for risk_level, count in risk_counts.items():
        percentage = (count / len(df)) * 100
        report_lines.append(f"• {risk_level} Risk: {count:,} properties ({percentage:.1f}%)")
    
    # Add flood zone analysis
    report_lines.extend([
        "",
        "FLOOD ZONE ANALYSIS:",
    ])
    
    flood_zone_counts = df['flood_zone'].value_counts()
    for zone, count in flood_zone_counts.items():
        percentage = (count / len(df)) * 100
        zone_at_risk = len(df[(df['flood_zone'] == zone) & (df['flood_depth'] > 0)])
        report_lines.append(f"• {zone}: {count:,} properties ({percentage:.1f}%), {zone_at_risk} at risk")
    
    # Save report
    report_file = output_path / 'flood_risk_summary.txt'
    with open(report_file, 'w') as f:
        f.write('\n'.join(report_lines))
    
    print(f"✅ Summary report saved: {report_file}")
    
    # Also print to console
    print("\n" + "\n".join(report_lines))

def main():
    """Main function to run flood risk visualization."""
    print("🚀 FLOOD RISK VISUALIZATION TOOL")
    print("=" * 40)
    
    # Debug paths first
    debug_paths()
    
    # Load property portfolio file from input directory
    property_portfolio_path = project_root / "input" / "property_portfolio.json"
    
    if not property_portfolio_path.exists():
        print(f"❌ File not found: {property_portfolio_path}")
        print("   Please ensure property_portfolio.json exists in the input/ directory")
        return False
    
    print(f"✅ Found property portfolio: {property_portfolio_path}")
    
    # Load and process data
    property_data = load_flood_data(property_portfolio_path)
    if not property_data:
        return False
    
    df = create_property_dataframe(property_data)
    if len(df) == 0:
        print("❌ No valid property data found")
        return False
    
    # Create output directory (using project_root/output)
    output_path = project_root / 'output'
    output_path.mkdir(exist_ok=True)
    
    print(f"📁 Output directory: {output_path}")
    print(f"📊 Processing {len(df)} properties...")
    
    # Generate all visualizations
    print("\n🗺️ Creating interactive map...")
    map_file = create_interactive_map(df, output_path)
    
    print("\n📈 Creating analysis charts...")
    create_analysis_charts(df, property_data, output_path)
    
    print("\n📝 Generating summary report...")
    generate_summary_report(df, property_data, output_path)
    
    # Auto-open the interactive map
    map_html_path = output_path / 'flood_risk_map.html'
    if map_html_path.exists():
        print(f"\n🚀 Auto-opening interactive map...")
        try:
            import webbrowser
            webbrowser.open(f'file://{map_html_path.absolute()}')
            print(f"✅ Opened in default browser: {map_html_path}")
        except Exception as e:
            print(f"❌ Could not auto-open browser: {e}")
            print(f"📂 Manual open: {map_html_path}")
    
    print(f"\n🎉 Complete! All files saved to: {output_path.absolute()}")
    print("\nFiles created:")
    print("• flood_risk_map.html - Interactive map (opened in browser)")
    print("• flood_risk_analysis.png - Analysis charts")
    print("• flood_risk_summary.txt - Summary report")
    
    return True

if __name__ == "__main__":
    main()