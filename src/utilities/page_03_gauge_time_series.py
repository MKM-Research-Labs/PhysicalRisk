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

# utilities/gauge_page_03_time_series_chart.py

"""
Gauge Time Series Chart Page Module
Creates water level vs time chart with flood threshold lines.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from io import BytesIO
from typing import Dict, Any, Optional, List
import pandas as pd

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


class GaugeTimeSeries:
    """Generate time series chart page for gauge reports."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.title_style = ParagraphStyle(
            'GaugeChartTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        self.subtitle_style = ParagraphStyle(
            'GaugeChartSubtitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=8,
            textColor=colors.darkblue
        )
    
    def generate_elements(self, gauge_data: Dict[str, Any], 
                         timeseries_data: Optional[List[Dict[str, Any]]] = None,
                         date_range: Optional[str] = None) -> List:
        """Generate page elements for time series chart."""
        elements = []
        
        # Page title
        gauge_name = gauge_data.get('Header', {}).get('GaugeName', 'Unknown Gauge')
        elements.append(Paragraph(f"Water Level Time Series", self.title_style))
        elements.append(Paragraph(f"Gauge: {gauge_name}", self.subtitle_style))
        elements.append(Spacer(1, 12))
        
        if not timeseries_data or len(timeseries_data) == 0:
            elements.append(Paragraph("No time series data available for this gauge.", self.styles['Normal']))
            return elements
        
        try:
            # Create the chart
            chart_image = self._create_time_series_chart(gauge_data, timeseries_data)
            if chart_image:
                elements.append(chart_image)
                elements.append(Spacer(1, 12))
            
            # Add summary statistics
            summary_table = self._create_summary_table(timeseries_data)
            if summary_table:
                elements.append(Paragraph("Time Series Summary", self.subtitle_style))
                elements.append(summary_table)
            
        except Exception as e:
            elements.append(Paragraph(f"Error generating chart: {str(e)}", self.styles['Normal']))
        
        return elements
    
    def _create_time_series_chart(self, gauge_data: Dict[str, Any], 
                                 timeseries_data: List[Dict[str, Any]]) -> Optional[Image]:
        """Create matplotlib chart and return as ReportLab Image."""
        try:
            # Extract data for plotting
            timestamps = []
            water_levels = []
            alert_levels = []
            warning_levels = []
            severe_levels = []
            
            for reading in timeseries_data:
                if 'timestamp' in reading and 'waterLevel' in reading:
                    timestamps.append(datetime.fromisoformat(reading['timestamp'].replace('Z', '+00:00')))
                    water_levels.append(reading['waterLevel'])
                    alert_levels.append(reading.get('alertLevel', 0))
                    warning_levels.append(reading.get('warningLevel', 0))
                    severe_levels.append(reading.get('severeLevel', 0))
            
            if not timestamps:
                return None
            
            # Create the plot
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Plot water levels
            ax.plot(timestamps, water_levels, 'b-', linewidth=2, label='Water Level', alpha=0.8)
            
            # Add threshold lines (use first reading's thresholds)
            if alert_levels and alert_levels[0] > 0:
                ax.axhline(y=alert_levels[0], color='green', linestyle='--', 
                          linewidth=1.5, alpha=0.7, label=f'Alert Level ({alert_levels[0]:.2f}m)')
            
            if warning_levels and warning_levels[0] > 0:
                ax.axhline(y=warning_levels[0], color='orange', linestyle='--', 
                          linewidth=1.5, alpha=0.7, label=f'Warning Level ({warning_levels[0]:.2f}m)')
            
            if severe_levels and severe_levels[0] > 0:
                ax.axhline(y=severe_levels[0], color='red', linestyle='--', 
                          linewidth=1.5, alpha=0.7, label=f'Severe Level ({severe_levels[0]:.2f}m)')
            
            # Add background shading between thresholds
            if alert_levels and warning_levels and severe_levels:
                y_min = min(min(water_levels), alert_levels[0] * 0.8)
                ax.fill_between(timestamps, y_min, alert_levels[0], 
                               color='lightgreen', alpha=0.2, label='Normal Zone')
                ax.fill_between(timestamps, alert_levels[0], warning_levels[0], 
                               color='yellow', alpha=0.2, label='Alert Zone')
                ax.fill_between(timestamps, warning_levels[0], severe_levels[0], 
                               color='orange', alpha=0.2, label='Warning Zone')
                y_max = max(max(water_levels), severe_levels[0] * 1.1)
                ax.fill_between(timestamps, severe_levels[0], y_max, 
                               color='red', alpha=0.2, label='Severe Zone')
            
            # Formatting
            gauge_name = gauge_data.get('Header', {}).get('GaugeName', 'Unknown Gauge')
            ax.set_title(f'{gauge_name} - Water Level Over Time', fontsize=14, fontweight='bold')
            ax.set_xlabel('Time', fontsize=12)
            ax.set_ylabel('Water Level (meters)', fontsize=12)
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
            plt.xticks(rotation=45)
            
            # Add grid
            ax.grid(True, alpha=0.3)
            
            # Add legend
            ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1))
            
            # Tight layout
            plt.tight_layout()
            
            # Convert to ReportLab Image
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # Create ReportLab Image
            image = Image(img_buffer, width=7*inch, height=4.2*inch)
            return image
            
        except Exception as e:
            print(f"Error creating time series chart: {e}")
            return None
    
    def _create_summary_table(self, timeseries_data: List[Dict[str, Any]]) -> Optional[Table]:
        """Create summary statistics table."""
        try:
            if not timeseries_data:
                return None
            
            # Calculate statistics
            water_levels = [r['waterLevel'] for r in timeseries_data if 'waterLevel' in r]
            if not water_levels:
                return None
            
            # Count alert status occurrences
            status_counts = {}
            for reading in timeseries_data:
                status = reading.get('alertStatus', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Get threshold values (from first reading)
            first_reading = timeseries_data[0]
            alert_level = first_reading.get('alertLevel', 'N/A')
            warning_level = first_reading.get('warningLevel', 'N/A')
            severe_level = first_reading.get('severeLevel', 'N/A')
            
            # Create table data
            table_data = [
                ['Statistic', 'Value'],
                ['Current Level', f"{water_levels[-1]:.2f}m" if water_levels else 'N/A'],
                ['Maximum Level', f"{max(water_levels):.2f}m"],
                ['Minimum Level', f"{min(water_levels):.2f}m"],
                ['Average Level', f"{sum(water_levels)/len(water_levels):.2f}m"],
                ['Total Readings', str(len(timeseries_data))],
                ['', ''],  # Separator
                ['Alert Level', f"{alert_level:.2f}m" if isinstance(alert_level, (int, float)) else str(alert_level)],
                ['Warning Level', f"{warning_level:.2f}m" if isinstance(warning_level, (int, float)) else str(warning_level)],
                ['Severe Level', f"{severe_level:.2f}m" if isinstance(severe_level, (int, float)) else str(severe_level)],
                ['', ''],  # Separator
                ['Normal Status Count', str(status_counts.get('Normal', 0))],
                ['Alert Status Count', str(status_counts.get('Alert', 0))],
                ['Warning Status Count', str(status_counts.get('Warning', 0))],
                ['Severe Status Count', str(status_counts.get('Severe', 0))],
            ]
            
            # Create table
            table = Table(table_data, colWidths=[2.5*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            return table
            
        except Exception as e:
            print(f"Error creating summary table: {e}")
            return None