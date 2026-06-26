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


"""Topology sensitivity — synthetic data + manifold-quality metrics.

Shared constants (SEED, FIGURES_DIR, MKM colours) and the two data
helpers used by the sensitivity runner."""

import logging

import numpy as np
from sklearn.datasets import make_classification

from config import config

logger = logging.getLogger(__name__)

SEED = 42
FIGURES_DIR = config.get_project_root() / "docs" / "models" / "Topology" / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

MKM_BLUE = "#1565C0"
MKM_RED = "#C62828"
MKM_GREY = "#616161"
MKM_LIGHT = "#E3F2FD"

def generate_weather_data(n_samples=2000, n_features=50, n_storm_types=5, seed=SEED):
    """
    Generate synthetic high-dimensional weather data mimicking HRRR fields.

    Features represent atmospheric variables (pressure, temperature, humidity,
    wind components) at multiple grid points. Storm types represent distinct
    meteorological regimes (frontal, convective, orographic, etc.).

    Returns:
        X: (n_samples, n_features) weather state matrix
        y_class: (n_samples,) storm type labels
        y_flood: (n_samples,) simulated flood depth (m)
    """
    rng = np.random.RandomState(seed)

    # Weather states with cluster structure (storm types)
    X, y_class = make_classification(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=20,
        n_redundant=15,
        n_clusters_per_class=2,
        n_classes=n_storm_types,
        random_state=seed,
    )

    # Add realistic noise (sensor/forecast uncertainty)
    X += rng.normal(0, 0.3, X.shape)

    # Simulate flood depth as nonlinear function of weather + terrain
    # This mimics the weather-to-flood mapping Psi
    terrain = rng.uniform(0, 1, n_samples)
    precip_proxy = X[:, :5].sum(axis=1)
    wind_proxy = X[:, 5:10].sum(axis=1)
    y_flood = (
        0.5 * np.tanh(precip_proxy)
        + 0.3 * terrain
        + 0.1 * np.abs(wind_proxy)
        + rng.normal(0, 0.05, n_samples)
    )
    y_flood = np.clip(y_flood, 0, 3.0)  # Physical bounds: 0-3m

    logger.info(
        "Generated %d weather samples: %d features, %d storm types, "
        "flood depth range [%.2f, %.2f] m",
        n_samples, n_features, n_storm_types,
        y_flood.min(), y_flood.max()
    )
    return X, y_class, y_flood

def compute_continuity(X_high, X_low, k=15):
    """
    Compute continuity metric C(k).

    Measures whether k-nearest neighbours in the HIGH-dimensional space
    are also neighbours in the low-dimensional space.
    (Complementary to trustworthiness which checks the reverse.)
    """
    from sklearn.neighbors import NearestNeighbors

    n = X_high.shape[0]
    nn_high = NearestNeighbors(n_neighbors=k + 1).fit(X_high)
    nn_low = NearestNeighbors(n_neighbors=k + 1).fit(X_low)

    _, idx_high = nn_high.kneighbors(X_high)
    _, idx_low = nn_low.kneighbors(X_low)

    # For each point, find neighbours in high-D that are NOT in low-D k-neighbourhood
    total = 0
    for i in range(n):
        high_neighbors = set(idx_high[i, 1:])
        low_neighbors = set(idx_low[i, 1:])
        missing = high_neighbors - low_neighbors

        for j in missing:
            # Rank of j in low-D
            rank_low = np.where(idx_low[i] == j)[0]
            if len(rank_low) > 0:
                total += rank_low[0] - k
            else:
                # j not in extended neighbourhood, use max rank
                dists = np.linalg.norm(X_low[i] - X_low[j])
                total += k  # conservative estimate

    normaliser = n * k * (2 * n - 3 * k - 1)
    if normaliser == 0:
        return 1.0
    return 1.0 - (2.0 / normaliser) * total
