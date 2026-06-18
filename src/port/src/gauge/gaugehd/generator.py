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

"""GaugeHistoricalDaily — thin facade delegating to sub-modules."""

from .nrfa import filter_by_years, generate_from_nrfa, parse_nrfa_csv
from .statistics import calculate_flow_statistics, calculate_level_statistics
from .synthetic import generate_from_gauge_portfolio, generate_synthetic_timeseries


class GaugeHistoricalDaily:
    """
    Generator for historical daily water level JSON files.

    Can generate synthetic timeseries from gauge portfolio data,
    or parse NRFA GDF CSV format when real data is available.
    """

    SCHEMA_VERSION = "1.0"

    def __init__(self, years_of_history: int = 50):
        self.years_of_history = years_of_history

    def generate_synthetic_timeseries(self, gauge_data, years=50, seed=None):
        return generate_synthetic_timeseries(gauge_data, years, seed)

    def calculate_statistics_from_levels(self, daily_observations, flood_stages):
        return calculate_level_statistics(daily_observations, flood_stages)

    def generate_from_gauge_portfolio(self, gauge_data, output_dir=None, years=None):
        years_to_use = years if years is not None else self.years_of_history
        return generate_from_gauge_portfolio(gauge_data, output_dir, years_to_use)

    def parse_nrfa_csv(self, filepath):
        return parse_nrfa_csv(filepath)

    def calculate_statistics(self, daily_flows):
        return calculate_flow_statistics(daily_flows)

    def filter_by_years(self, daily_flows, years=None):
        return filter_by_years(daily_flows, years)

    def generate_from_nrfa(self, input_path, output_path=None, years=None, gauge_id=None):
        years_to_use = years if years is not None else self.years_of_history
        return generate_from_nrfa(input_path, output_path, years_to_use, gauge_id)
