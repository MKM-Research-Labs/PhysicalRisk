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

"""Public API — classifiers (binary GBM models, one per gauge)."""

from __future__ import annotations

from .backend import active_backend


def list_classifier_ids(catchment) -> list[str]:
    return list(active_backend().iter_keys("classifier", catchment))


def get_classifier(catchment, gauge_id) -> bytes | None:
    try:
        return active_backend().load("classifier", catchment, gauge_id)
    except (FileNotFoundError, KeyError):
        return None


def save_classifier(catchment, gauge_id, blob: bytes):   # -> @require("Func004", "create")
    active_backend().save("classifier", catchment, blob, gauge_id)


def delete_classifier(catchment, gauge_id):              # -> @require("Func004", "delete")
    active_backend().delete("classifier", catchment, gauge_id)


# ── Classifier training metadata (summary + timings documents) ────────────────
def get_classifier_training_summary(catchment):
    try:
        return active_backend().load("classifier_training_summary", catchment)
    except (FileNotFoundError, KeyError):
        return None

def save_classifier_training_summary(catchment, payload):
    active_backend().save("classifier_training_summary", catchment, payload)

def delete_classifier_training_summary(catchment):
    active_backend().delete("classifier_training_summary", catchment)

def get_classifier_timings(catchment):
    try:
        return active_backend().load("classifier_timings", catchment)
    except (FileNotFoundError, KeyError):
        return None

def save_classifier_timings(catchment, payload):
    active_backend().save("classifier_timings", catchment, payload)

def delete_classifier_timings(catchment):
    active_backend().delete("classifier_timings", catchment)
