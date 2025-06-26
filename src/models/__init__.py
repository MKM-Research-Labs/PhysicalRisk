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
Models Package.

This package contains core modeling functionality for different risk domains,
including flood risk, portfolio analysis, and terrain modeling.

The PortfolioFloodModel now includes integrated flood risk analysis functionality,
consolidating previously separate flood risk models into a unified interface.
"""

from .portfolio_flood_model import PortfolioFloodModel

__all__ = [
    'PortfolioFloodModel',
]

# Legacy compatibility - in case other code still tries to import FloodRiskModel
# This provides a deprecation path
def FloodRiskModel(*args, **kwargs):
    """
    Deprecated: Use PortfolioFloodModel instead.
    FloodRiskModel functionality has been merged into PortfolioFloodModel.
    """
    import warnings
    warnings.warn(
        "FloodRiskModel is deprecated. Use PortfolioFloodModel instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return PortfolioFloodModel(*args, **kwargs)

def FloodRiskReport(*args, **kwargs):
    """
    Deprecated: Use PortfolioFloodModel.generate_comprehensive_report() instead.
    """
    import warnings
    warnings.warn(
        "FloodRiskReport is deprecated. Use PortfolioFloodModel.generate_comprehensive_report() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    # Return a placeholder or raise an exception
    raise NotImplementedError("FloodRiskReport functionality moved to PortfolioFloodModel.generate_comprehensive_report()")