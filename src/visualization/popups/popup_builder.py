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
Common popup utilities and base popup builder.

This module provides base functionality and utilities shared across
different popup types in the visualization system.
"""

from typing import Dict, Any, Optional, List
import folium


class PopupBuilder:
    """Base class for building popups with common utilities."""
    
    def __init__(self):
        """Initialize the popup builder."""
        pass
    
    def create_section(self, title: str, content: str, background_color: str = "#EBF5FB", 
                      title_color: str = "#1a5276") -> str:
        """
        Create a styled section for a popup.
        
        Args:
            title: Section title
            content: Section content (HTML)
            background_color: Background color for the section
            title_color: Color for the section title
            
        Returns:
            HTML string for the section
        """
        return f"""
        <div style="background-color: {background_color}; padding: 10px; border-radius: 5px; margin-top: 10px;">
            <h5 style="margin-top: 0; color: {title_color};">{title}</h5>
            {content}
        </div>
        """
    
    def create_header(self, title: str, subtitle: str = "", main_color: str = "#1a5276") -> str:
        """
        Create a popup header.
        
        Args:
            title: Main title
            subtitle: Optional subtitle
            main_color: Color for the title
            
        Returns:
            HTML string for the header
        """
        subtitle_html = f'<p style="color: #566573; font-size: 0.9em;">{subtitle}</p>' if subtitle else ""
        
        return f"""
        <h4 style="margin-bottom: 5px; color: {main_color};">{title}</h4>
        {subtitle_html}
        """
    
    def create_data_row(self, label: str, value: Any, bold_label: bool = True) -> str:
        """
        Create a data row for display in popups.
        
        Args:
            label: Data label
            value: Data value
            bold_label: Whether to make the label bold
            
        Returns:
            HTML string for the data row
        """
        label_style = "font-weight: bold;" if bold_label else ""
        return f'<p><span style="{label_style}">{label}:</span> {value}</p>'
    
    def safe_format_float(self, value: Any, decimals: int = 2) -> str:
        """
        Safely format a value as float.
        
        Args:
            value: Value to format
            decimals: Number of decimal places
            
        Returns:
            Formatted string or "N/A" if formatting fails
        """
        if value in [None, "N/A", ""]:
            return "N/A"
        try:
            return f"{float(value):.{decimals}f}"
        except (ValueError, TypeError):
            return str(value)
    
    def format_currency(self, amount: Any, symbol: str = "£") -> str:
        """
        Format a value as currency.
        
        Args:
            amount: Amount to format
            symbol: Currency symbol
            
        Returns:
            Formatted currency string
        """
        if amount in [None, "N/A", "", "Unknown"]:
            return "Not available"
        
        try:
            if isinstance(amount, (int, float)):
                return f"{symbol}{amount:,.2f}"
            else:
                return f"{symbol}{float(amount):,.2f}"
        except (ValueError, TypeError):
            return str(amount)
    
    def format_percentage(self, value: Any, decimals: int = 1) -> str:
        """
        Format a value as percentage.
        
        Args:
            value: Value to format (0-1 for decimal, >1 for percentage)
            decimals: Number of decimal places
            
        Returns:
            Formatted percentage string
        """
        if value in [None, "N/A", ""]:
            return "N/A"
        
        try:
            num_value = float(value)
            if num_value < 1:
                return f"{num_value * 100:.{decimals}f}%"
            else:
                return f"{num_value:.{decimals}f}%"
        except (ValueError, TypeError):
            return str(value)
    
    def get_risk_color(self, risk_level: str) -> str:
        """
        Get color for risk level display.
        
        Args:
            risk_level: Risk level string
            
        Returns:
            Color code for the risk level
        """
        risk_colors = {
            'Very low': 'green',
            'Very Low': 'green',
            'Low': 'lightgreen',
            'Medium': 'orange',
            'High': 'red',
            'Very high': 'darkred',
            'Very High': 'darkred'
        }
        return risk_colors.get(risk_level, 'blue')
    
    def create_colored_text(self, text: str, color: str, bold: bool = False) -> str:
        """
        Create colored text span.
        
        Args:
            text: Text content
            color: Text color
            bold: Whether to make text bold
            
        Returns:
            HTML span with styled text
        """
        style = f"color: {color};"
        if bold:
            style += " font-weight: bold;"
        
        return f'<span style="{style}">{text}</span>'
    
    def create_popup_wrapper(self, content: str, max_width: int = 320, max_height: int = 400) -> str:
        """
        Create the main wrapper div for popup content.
        
        Args:
            content: Popup content HTML
            max_width: Maximum width in pixels
            max_height: Maximum height in pixels
            
        Returns:
            Complete HTML string with wrapper
        """
        return f"""
        <div style="font-family: Arial; width: {max_width}px; max-height: {max_height}px; overflow-y: auto;">
            {content}
        </div>
        """
    
    def build_popup(self, content: str, max_width: int = 350) -> folium.Popup:
        """
        Build a Folium popup with the given content.
        
        Args:
            content: HTML content for the popup
            max_width: Maximum width of the popup
            
        Returns:
            Folium Popup object
        """
        return folium.Popup(content, max_width=max_width)