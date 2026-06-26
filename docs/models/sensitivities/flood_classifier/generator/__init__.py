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

"""Flood Probability Classifier (GBM) sensitivity analysis.

Trains GBM classifiers with varied hyperparameters on actual stress
test vectors and reports AUC-ROC and accuracy metrics.
"""

import json
import os

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score

from docs.models.sensitivities import latex_table, write_tables

from config import config

_project_root = str(config.get_project_root())


def _load_sample_gauge():
    """Load a representative gauge's training data for sensitivity runs.

    Uses the training summary to pick a gauge, then regenerates vectors
    on the fly (since bulk vectors are no longer persisted to disk).
    """
    import sys
    sys.path.insert(0, os.path.join(_project_root, 'src'))
    from port.src.stress import (
        _synthesize_hydrograph, _noise_sigma, NUM_HOURS,
        TARGET_NON_ALERT,
    )

    input_dir = os.path.join(str(config.get_input_root()), 'thames')

    # Pick first gauge from training summary
    summary_path = os.path.join(
        _project_root, 'data', 'output', 'stress', 'training_summary.json')
    with open(summary_path) as f:
        ts = json.load(f)
    trained = [g for g in ts['gauges'] if g['status'] == 'trained']
    if not trained:
        raise RuntimeError("No trained gauges found")
    target = trained[0]
    gauge_id = target['gauge_id']

    # Regenerate vectors for this gauge (same logic as stress generator)
    rng = np.random.RandomState(42)

    with open(os.path.join(input_dir, 'storms.json')) as f:
        all_storms = {s['storm_id']: s for s in json.load(f)['storms']}
    # Load alert storm IDs from index (directory layout) or legacy single file
    _ss_index = os.path.join(input_dir, 'stress_storms', '_index.json')
    _ss_legacy = os.path.join(input_dir, 'stress_storms.json')
    _ss_path = _ss_index if os.path.exists(_ss_index) else _ss_legacy
    with open(_ss_path) as f:
        alert_ids = {s['storm_id'] for s in json.load(f)['storms']}
    non_alert = [s for s in all_storms if s not in alert_ids]
    n_sample = min(TARGET_NON_ALERT, len(non_alert))
    sampled = set(rng.choice(non_alert, size=n_sample, replace=False))
    selected = alert_ids | sampled

    gaugets_path = os.path.join(input_dir, 'gaugets', f'{gauge_id}.json')
    with open(gaugets_path) as f:
        gdata = json.load(f)
    resp_lookup = {r['storm_id']: r
                   for r in gdata.get('storm_responses', {}).get('responses', [])}

    vectors = []
    for storm_id in sorted(selected):
        resp = resp_lookup.get(storm_id)
        storm_info = all_storms.get(storm_id)
        if not resp or not storm_info:
            continue
        flood_flag = 1 if resp.get('exceeded_alert', False) else 0
        hydro = _synthesize_hydrograph(
            resp['base_level_m'], resp['level_change_m'],
            storm_info['duration_hours'], storm_info['peak_position'])
        for h in range(NUM_HOURS):
            sigma = _noise_sigma(h)
            noisy = hydro[h] + rng.normal(0, sigma)
            vectors.append([round(noisy, 4), h, flood_flag])

    X = np.array([[v[0], v[1]] for v in vectors])
    y = np.array([v[2] for v in vectors])
    return gauge_id, X, y


def _train_and_score(X_train, y_train, X_test, y_test, **kwargs):
    """Train a GBM with given kwargs and return (AUC, accuracy)."""
    defaults = dict(n_estimators=200, max_depth=4, learning_rate=0.1,
                    subsample=0.8, min_samples_leaf=20, random_state=42)
    defaults.update(kwargs)
    model = GradientBoostingClassifier(**defaults)
    model.fit(X_train, y_train)
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)
    return round(roc_auc_score(y_test, y_prob), 4), round(accuracy_score(y_test, y_pred), 4)


def generate():
    """Generate flood classifier sensitivity tables from actual model training."""
    gauge_id, X, y = _load_sample_gauge()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)

    print(f'  Using gauge {gauge_id} ({len(X)} samples, flood rate {y.mean():.3f})')

    # Table 1: n_estimators sensitivity (default=200)
    print('  Training n_estimators variants...')
    rows = []
    for n in [50, 100, 200, 500]:
        auc, acc = _train_and_score(X_train, y_train, X_test, y_test,
                                    n_estimators=n)
        note = '\\textbf{Production}' if n == 200 else ''
        rows.append([n, f'{auc:.4f}', f'{acc:.4f}', note])

    t1 = latex_table(
        f'Classifier sensitivity to n\\_estimators (gauge {gauge_id[:10]}, '
        f'max\\_depth=4, lr=0.1).',
        'sens_n_estimators',
        ['n\\_estimators', 'AUC-ROC', 'Accuracy', ''], rows,
        col_fmt='rccl',
    )

    # Table 2: max_depth sensitivity (default=4)
    print('  Training max_depth variants...')
    rows = []
    for d in [2, 3, 4, 5, 6]:
        auc, acc = _train_and_score(X_train, y_train, X_test, y_test,
                                    max_depth=d)
        note = '\\textbf{Production}' if d == 4 else ''
        rows.append([d, f'{auc:.4f}', f'{acc:.4f}', note])

    t2 = latex_table(
        f'Classifier sensitivity to max\\_depth (gauge {gauge_id[:10]}, '
        f'n\\_estimators=200, lr=0.1).',
        'sens_max_depth',
        ['max\\_depth', 'AUC-ROC', 'Accuracy', ''], rows,
        col_fmt='rccl',
    )

    # Table 3: learning_rate sensitivity (default=0.1)
    print('  Training learning_rate variants...')
    rows = []
    for lr in [0.01, 0.05, 0.10, 0.20, 0.50]:
        auc, acc = _train_and_score(X_train, y_train, X_test, y_test,
                                    learning_rate=lr)
        note = '\\textbf{Production}' if lr == 0.10 else ''
        rows.append([lr, f'{auc:.4f}', f'{acc:.4f}', note])

    t3 = latex_table(
        f'Classifier sensitivity to learning\\_rate (gauge {gauge_id[:10]}, '
        f'n\\_estimators=200, max\\_depth=4).',
        'sens_learning_rate',
        ['learning\\_rate', 'AUC-ROC', 'Accuracy', ''], rows,
        col_fmt='rccl',
    )

    # Table 4: subsample sensitivity (default=0.8)
    print('  Training subsample variants...')
    rows = []
    for ss in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        auc, acc = _train_and_score(X_train, y_train, X_test, y_test,
                                    subsample=ss)
        note = '\\textbf{Production}' if ss == 0.8 else ''
        rows.append([ss, f'{auc:.4f}', f'{acc:.4f}', note])

    t4 = latex_table(
        f'Classifier sensitivity to subsample fraction (gauge {gauge_id[:10]}, '
        f'n\\_estimators=200, max\\_depth=4, lr=0.1).',
        'sens_subsample',
        ['subsample', 'AUC-ROC', 'Accuracy', ''], rows,
        col_fmt='rccl',
    )

    # Table 5: Feature importance at production config
    print('  Extracting feature importance...')
    model = GradientBoostingClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.1,
        subsample=0.8, min_samples_leaf=20, random_state=42)
    model.fit(X_train, y_train)
    fi = model.feature_importances_
    rows = [
        ['water\\_level', f'{fi[0]:.4f}'],
        ['hour', f'{fi[1]:.4f}'],
    ]
    t5 = latex_table(
        f'Feature importance at production hyperparameters (gauge {gauge_id[:10]}).',
        'sens_feature_importance',
        ['Feature', 'Importance'], rows,
        col_fmt='lr',
    )

    write_tables('flood_classifier', '\n\n'.join([t1, t2, t3, t4, t5]))
