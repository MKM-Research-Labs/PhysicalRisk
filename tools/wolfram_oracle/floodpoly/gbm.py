# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""FPO-001 against the GBM classifiers it approximates (MKM-FC-001).

The polynomial sees the level and the hour; each gauge's GBM also sees the rate of
rise. So the comparison is made where production uses it: on the real storm states
the classifiers are trained on, rebuilt by the challenger's catalogue loader, below
severe (at and above it P = 1). The same states give the support envelope -- the
earliest hour any storm reached each level -- and the document's held-out table is
recomputed on the fit's own split, with the document's model.
"""

import io

import joblib
import numpy as np

from config.models import ORACLE_FPO_DOC_HOURS, ORACLE_FPO_NEAR, ORACLE_FPO_SEED, ORACLE_FPO_STORMS


def catalogue(gauge_ids, n_storms):  # pragma: no cover - reads the data store
    """Real storm states per gauge: (gauge_id, X, y), X = [h, t, dh, d2h]."""
    from tools.flood_classifier_challenger._data import load_catalogue
    for gs in load_catalogue(gauge_ids, n_storms=n_storms, seed=ORACLE_FPO_SEED):
        yield gs.gauge_id, gs.X[:gs.n_real], gs.y[:gs.n_real]


def classifier(gauge_id):  # pragma: no cover - reads the data store
    """A gauge's production classifier, read as production reads it."""
    import database
    from database.config_binding import use_configured_backend
    use_configured_backend()
    return joblib.load(io.BytesIO(database.get_classifier(database.active_catchment(), gauge_id)))


def gauge_ids():  # pragma: no cover - reads the data store
    import database
    from database.config_binding import use_configured_backend
    use_configured_backend()
    return sorted(database.list_classifier_ids(database.active_catchment()))


def _stats(p, g, y):
    d = p - g
    return {"n": int(len(d)), "mae": float(np.abs(d).mean()), "bias": float(d.mean()),
            "p95": float(np.quantile(np.abs(d), 0.95)) if len(d) else 0.0,
            "over": float((np.abs(d) > 0.1).mean()) if len(d) else 0.0,
            "over05": float((np.abs(d) > 0.05).mean()) if len(d) else 0.0,
            "gbm": float(g.mean()), "poly": float(p.mean()), "label": float(y.mean())}


def compare(predict, ids=None, n_storms=ORACLE_FPO_STORMS):
    """Per gauge, the polynomial (``predict(h, t)``) against the GBM below severe and
    near it; and the highest level any storm reached by each hour."""
    out, top = [], np.full(ORACLE_FPO_DOC_HOURS, -np.inf)
    for gid, X, y in catalogue(ids if ids is not None else gauge_ids(), n_storms):
        g = classifier(gid).predict_proba(X)[:, 1]
        p = predict(X[:, 0], X[:, 1])
        below = X[:, 0] < 0
        near = below & (X[:, 0] >= np.log(ORACLE_FPO_NEAR))
        out.append({"gauge": gid, "below": _stats(p[below], g[below], y[below]),
                    "near": _stats(p[near], g[near], y[near])})
        hour = np.rint(np.exp(X[:, 1]) * ORACLE_FPO_DOC_HOURS - 1).astype(int)
        np.maximum.at(top, hour, X[:, 0])
    return out, np.exp(np.maximum.accumulate(top))


def first_reached(top, ratio):
    """The hour a level is first reached, linear between hours, from the highest level by hour."""
    k = int(np.argmax(top >= ratio))
    if top[k] < ratio:
        return None
    return 0.0 if k == 0 or top[0] >= ratio else k - 1 + (ratio - top[k - 1]) / (top[k] - top[k - 1])


def heldout(predict):
    """Per gauge, on the storms the fit did not see: (near MAE, near bias, near share
    over 0.1, below MAE) of ``predict`` against the GBM, and the fit and test counts."""
    from tools.flood_poly_fit.fit import states
    h, t, g, gauge, is_fit = states()
    test = ~is_fit
    p = predict(h[test], t[test])
    rows = []
    for k in np.unique(gauge[test]):
        m = gauge[test] == k
        nm = m & (h[test] >= np.log(ORACLE_FPO_NEAR))
        d = p - g[test]
        rows.append((float(np.abs(d[nm]).mean()), float(d[nm].mean()), float((np.abs(d[nm]) > 0.1).mean()),
                     float(np.abs(d[m]).mean())))
    return {"rows": rows, "fit_states": int(is_fit.sum()), "test_states": int(test.sum())}
